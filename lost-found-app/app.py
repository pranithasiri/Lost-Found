from flask import Flask, render_template, request, redirect, url_for
import json
import os

app = Flask(__name__)

DATA_FILE = "database/data.json"


# ------------------ HELPERS ------------------

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


def generate_id(data):
    all_items = data["lost_items"] + data["found_items"]
    return len(all_items) + 1


def find_match(new_item, items_list):
    for item in items_list:
        if (
            item["name"].lower() == new_item["name"].lower()
            and item["location"].lower() == new_item["location"].lower()
        ):
            return True
    return False


# ------------------ ROUTES ------------------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        return redirect(url_for("dashboard"))
    return render_template("register.html")


@app.route("/dashboard")
def dashboard():
    data = load_data()
    items = data["lost_items"] + data["found_items"]
    return render_template("dashboard.html", items=items)


# ------------------ REPORT LOST ------------------

@app.route("/report_lost", methods=["GET", "POST"])
def report_lost():
    if request.method == "POST":
        data = load_data()

        name = request.form.get("name")
        description = request.form.get("description")
        location = request.form.get("location")

        username = request.form.get("username") or "Anonymous"
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

        # check match with found items
        match = find_match(new_item, data["found_items"])

        data["lost_items"].append(new_item)
        save_data(data)

        if match:
            return render_template("success.html", message="Match Found!", is_match=True)
        else:
            return render_template("success.html", message="Item Submitted Successfully", is_match=False)

    return render_template("report_lost.html")


# ------------------ REPORT FOUND ------------------

@app.route("/report_found", methods=["GET", "POST"])
def report_found():
    if request.method == "POST":
        data = load_data()

        name = request.form.get("name")
        description = request.form.get("description")
        location = request.form.get("location")

        username = request.form.get("username") or "Anonymous"
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

        # check match with lost items
        match = find_match(new_item, data["lost_items"])

        data["found_items"].append(new_item)
        save_data(data)

        if match:
            return render_template("success.html", message="Match Found!", is_match=True)
        else:
            return render_template("success.html", message="Item Submitted Successfully", is_match=False)

    return render_template("report_found.html")


# ------------------ VIEW ITEM ------------------

@app.route("/item/<int:item_id>")
def view_item(item_id):
    data = load_data()
    all_items = data["lost_items"] + data["found_items"]

    item = next((i for i in all_items if i["id"] == item_id), None)

    if item:
        return render_template("view_item.html", item=item)
    else:
        return "Item not found", 404


# ------------------ RUN ------------------

if __name__ == "__main__":
    app.run(debug=True)

import boto3

sns = boto3.client('sns')

from flask import request, jsonify
from flask import Flask, render_template, request, redirect, session
import boto3

@app.route("/alert", methods=["POST"])
def alert_owner():
    data_json = request.get_json()
    item_id = data_json["item_id"]

    data = load_data()
    all_items = data["lost_items"] + data["found_items"]

    for item in all_items:
        if item["id"] == item_id:
            email = item.get("email")

            if email:
                sns.publish(
                    TopicArn="YOUR_SNS_TOPIC_ARN",
                    Message=f"Someone is interested in your item: {item['name']}",
                    Subject="Lost & Found Alert"
                )
            break

    return jsonify({"status": "success"})
    item_id = request.form["item_id"]
    data = load_data()

    all_items = data["lost_items"] + data["found_items"]

    for item in all_items:
        if item["id"] == item_id:
            email = item.get("email")

            if email:
                sns.publish(
                    TopicArn="YOUR_SNS_TOPIC_ARN",
                    Message=f"Someone is interested in your item: {item['name']}",
                    Subject="Lost & Found Alert"
                )
            break

    return redirect("/dashboard?alert=success")
    data = load_data()

    all_items = data["lost_items"] + data["found_items"]

    for item in all_items:
        if item["id"] == item_id:
            email = item.get("email")

            if email:
                sns.publish(
                    TopicArn="YOUR_SNS_TOPIC_ARN",
                    Message=f"Someone is interested in your item: {item['name']}",
                    Subject="Lost & Found Alert"
                )

            break

    return redirect("/dashboard")