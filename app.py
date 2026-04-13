from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import boto3
from dotenv import load_dotenv

# ------------------ INIT ------------------

app = Flask(__name__)
app.secret_key = "your_secret_key"

load_dotenv()

# ------------------ AWS SETUP ------------------

dynamodb = boto3.resource(
    'dynamodb',
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

sns = boto3.client(
    'sns',
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN")

lost_table_name = "lost_items"
found_table_name = "found_items"
users_table_name = "users"

# ------------------ CREATE TABLES ------------------

def create_table_if_not_exists(table_name):
    existing_tables = dynamodb.meta.client.list_tables()['TableNames']

    if table_name in existing_tables:
        return

    if table_name == "users":
        key_schema = [{'AttributeName': 'email', 'KeyType': 'HASH'}]
        attr_def = [{'AttributeName': 'email', 'AttributeType': 'S'}]
    else:
        key_schema = [{'AttributeName': 'id', 'KeyType': 'HASH'}]
        attr_def = [{'AttributeName': 'id', 'AttributeType': 'N'}]

    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=key_schema,
        AttributeDefinitions=attr_def,
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )

    table.wait_until_exists()
    print(f"{table_name} created")

create_table_if_not_exists(lost_table_name)
create_table_if_not_exists(found_table_name)
create_table_if_not_exists(users_table_name)

lost_table = dynamodb.Table(lost_table_name)
found_table = dynamodb.Table(found_table_name)
users_table = dynamodb.Table(users_table_name)

# ------------------ HELPERS ------------------

def load_data():
    return {
        "lost_items": lost_table.scan().get('Items', []),
        "found_items": found_table.scan().get('Items', [])
    }

def generate_id(data):
    return int(len(data["lost_items"] + data["found_items"]) + 1)

def get_user_details(email):
    response = users_table.get_item(Key={"email": email})
    return response.get("Item")

def find_match(new_item, items_list):
    for item in items_list:
        if (
            item["name"].lower() == new_item["name"].lower()
            and item["location"].lower() == new_item["location"].lower()
        ):
            return item
    return None

def send_match_notification(lost_item, found_item):
    lost_user = get_user_details(lost_item["email"])
    found_user = get_user_details(found_item["email"])

    if not lost_user or not found_user:
        return

    # Lost user message
    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject="Your Lost Item Found!",
        Message=f"""
Hello {lost_user['name']},

Good news!

Your item "{lost_item['name']}" has been found by {found_user['name']}.

Location: {found_item['location']}

Check your dashboard.

- Lost & Found System
"""
    )

    # Found user message
    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject="Someone is looking for your item!",
        Message=f"""
Hello {found_user['name']},

Someone is searching for the item you found.

Item: {found_item['name']}
Lost by: {lost_user['name']}

Check your dashboard.

- Lost & Found System
"""
    )

# ------------------ ROUTES ------------------

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = users_table.get_item(Key={"email": email}).get("Item")

        if user and user["password"] == password:
            session["email"] = email
            return redirect(url_for("dashboard"))
        return "Invalid credentials"

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        users_table.put_item(Item={
            "email": email,
            "name": name,
            "password": password
        })

        session["email"] = email
        return redirect(url_for("dashboard"))

    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    data = load_data()
    return render_template("dashboard.html", items=data["lost_items"] + data["found_items"])

# ------------------ REPORT LOST ------------------

@app.route("/report_lost", methods=["GET", "POST"])
def report_lost():
    if request.method == "POST":
        data = load_data()

        name = request.form.get("name")
        description = request.form.get("description")
        location = request.form.get("location")

        user = get_user_details(session.get("email"))
        username = user["name"] if user else "Anonymous"

        image = request.files.get("image")
        filename = ""

        if image and image.filename != "":
            filename = image.filename
            image.save(os.path.join("static", filename))

        new_item = {
            "id": generate_id(data),
            "name": name,
            "description": description,
            "location": location,
            "image": filename,
            "username": username,
            "type": "lost",
            "email": session.get("email")
        }

        match = find_match(new_item, data["found_items"])

        lost_table.put_item(Item=new_item)

        if match:
            send_match_notification(new_item, match)
            return render_template("success.html", message="Match Found!", is_match=True)

        return render_template("success.html", message="Item Submitted", is_match=False)

    return render_template("report_lost.html")

# ------------------ REPORT FOUND ------------------

@app.route("/report_found", methods=["GET", "POST"])
def report_found():
    if request.method == "POST":
        data = load_data()

        name = request.form.get("name")
        description = request.form.get("description")
        location = request.form.get("location")

        user = get_user_details(session.get("email"))
        username = user["name"] if user else "Anonymous"

        image = request.files.get("image")
        filename = ""

        if image and image.filename != "":
            filename = image.filename
            image.save(os.path.join("static", filename))

        new_item = {
            "id": generate_id(data),
            "name": name,
            "description": description,
            "location": location,
            "image": filename,
            "username": username,
            "type": "found",
            "email": session.get("email")
        }

        match = find_match(new_item, data["lost_items"])

        found_table.put_item(Item=new_item)

        if match:
            send_match_notification(match, new_item)
            return render_template("success.html", message="Match Found!", is_match=True)

        return render_template("success.html", message="Item Submitted", is_match=False)

    return render_template("report_found.html")

# ------------------ VIEW ITEM ------------------

@app.route("/item/<int:item_id>")
def view_item(item_id):
    data = load_data()
    items = data["lost_items"] + data["found_items"]

    item = next((i for i in items if i["id"] == item_id), None)

    if item:
        return render_template("view_item.html", item=item)
    return "Item not found", 404

# ------------------ ALERT OWNER ------------------

@app.route("/alert", methods=["POST"])
def alert_owner():
    try:
        data = request.get_json(force=True)  # 🔥 FORCE JSON

        item_id = int(data["item_id"])

        data_all = load_data()
        all_items = data_all["lost_items"] + data_all["found_items"]

        for item in all_items:
            if int(item["id"]) == item_id:
                user = get_user_details(item["email"])

                if user:
                        # Get current logged-in user (who clicked alert)
                        current_user = get_user_details(session.get("email"))
                        sender_name = current_user["name"] if current_user else "Someone"
                
                        sns.publish(
                        TopicArn=SNS_TOPIC_ARN,
                        Subject="Lost & Found Alert",
                        Message=f"""
                                Hello {user['name']}, 
                                {sender_name} is interested in your item.
                                Item: {item['name']}
                                Location: {item['location']}
                                This is user's email: {session.get("email")}
                                - Lost & Found System
                                """
                        )
                break

        return jsonify({"status": "success"})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

# ------------------ LOGOUT ------------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# ------------------ RUN ------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

