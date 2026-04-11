from flask import Flask, render_template, request, redirect, url_for
import json

app = Flask(__name__)

DATA_FILE = "database/data.json"

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def find_match(new_item, items_list):
    for item in items_list:
        if (
            item["name"].lower() == new_item["name"].lower()
            and item["location"].lower() == new_item["location"].lower()
        ):
            return True
    return False

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
    return render_template("dashboard.html")

@app.route("/report-lost", methods=["GET", "POST"])
def report_lost():
    if request.method == "POST":
        data = load_data()

        item = {
            "name": request.form.get("item_name"),
            "description": request.form.get("description"),
            "location": request.form.get("location")
        }

        # ?? check match with found items
        match = find_match(item, data["found_items"])

        data["lost_items"].append(item)
        save_data(data)

        if match:
            return render_template("success.html", message="Match Found!", is_match=True)
        else:
            return render_template("success.html", message="Item Submitted Successfully", is_match=False)

    return render_template("report_lost.html")


@app.route("/report-found", methods=["GET", "POST"])
def report_found():
    if request.method == "POST":
        data = load_data()

        item = {
            "name": request.form.get("item_name"),
            "description": request.form.get("description"),
            "location": request.form.get("location")
        }

        # ?? check match with lost items
        match = find_match(item, data["lost_items"])

        data["found_items"].append(item)
        save_data(data)

        if match:
            return render_template("success.html", message="Match Found!", is_match=True)
        else:
            return render_template("success.html", message="Item Submitted Successfully", is_match=False)

    return render_template("report_found.html")

if __name__ == "__main__":
    app.run(debug=True)
