from flask import Flask, request, jsonify, render_template_string
from groq import Groq
import os
import re

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VAID Adaptive AI Triage</title>

<style>
body {
    margin:0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background:#f8c8dc;
    color:#222;
}

.container {
    max-width:700px;
    margin:auto;
    padding:20px;
}

h1 {
    text-align:center;
    font-size:26px;
    margin-bottom:20px;
}

.card {
    background:white;
    padding:20px;
    border-radius:18px;
    margin-top:20px;
    box-shadow:0 4px 12px rgba(0,0,0,0.08);
}

button {
    width:100%;
    padding:14px;
    margin-top:12px;
    border:none;
    border-radius:14px;
    font-size:16px;
    cursor:pointer;
}

.primary {
    background:#d63384;
    color:white;
}

.secondary {
    background:#eee;
}

input, select {
    width:100%;
    padding:12px;
    margin-top:8px;
    border-radius:10px;
    border:1px solid #ccc;
    font-size:15px;
}

.checkbox-group {
    display:flex;
    align-items:center;
    gap:10px;
    margin-top:10px;
}

.checkbox-group input {
    width:auto;
}

.hidden { display:none; }

.result-box {
    font-size:17px;
    line-height:1.6;
}

.risk-low { color:green; font-weight:bold; }
.risk-medium { color:orange; font-weight:bold; }
.risk-high { color:red; font-weight:bold; }
.risk-emergency { color:darkred; font-weight:bold; font-size:20px; }

</style>
</head>
<body>

<div class="container">

<h1>VAID Adaptive AI Triage</h1>

<div id="languageCard" class="card">
    <button class="primary" onclick="setLanguage('english')">English</button>
    <button class="secondary" onclick="setLanguage('hindi')">हिन्दी</button>
</div>

<div id="formCard" class="card hidden">

    <h3 id="profileTitle">Basic Profile</h3>
    <input type="number" id="age" placeholder="Age">

    <select id="sex" onchange="checkPregnancy()">
        <option value="">Sex</option>
        <option>Male</option>
        <option>Female</option>
        <option>Other</option>
    </select>

    <div id="pregnancyDiv" class="hidden">
        <select id="pregnant">
            <option value="">Pregnant?</option>
            <option>Yes</option>
            <option>No</option>
        </select>
    </div>

    <input type="number" id="height" placeholder="Height (cm)">
    <input type="number" id="weight" placeholder="Weight (kg)">

    <h3>Main Symptoms</h3>

    <div class="checkbox-group"><input type="checkbox" value="Fever" class="symptom"> Fever</div>
    <div class="checkbox-group"><input type="checkbox" value="Chest pain" class="symptom"> Chest pain</div>
    <div class="checkbox-group"><input type="checkbox" value="Shortness of breath" class="symptom"> Shortness of breath</div>
    <div class="checkbox-group"><input type="checkbox" value="Severe headache" class="symptom"> Severe headache</div>
    <div class="checkbox-group"><input type="checkbox" value="Heavy bleeding" class="symptom"> Heavy bleeding</div>
    <div class="checkbox-group"><input type="checkbox" value="Abdominal pain" class="symptom"> Abdominal pain</div>
    <div class="checkbox-group"><input type="checkbox" value="Vomiting" class="symptom"> Vomiting</div>

    <h3>Pain Severity (1-10)</h3>
    <input type="number" id="pain" min="1" max="10">

    <button class="primary" onclick="analyze()">Analyze</button>

</div>

<div id="resultCard" class="card hidden result-box"></div>

</div>

<script>

let language = "english";

const uiText = {
    english: {
        profile: "Basic Profile",
        symptoms: "Main Symptoms",
        pain: "Pain Severity (1-10)",
        analyze: "Analyze",
        assessment: "Assessment",
        condition: "Condition",
        risk: "Risk",
        action: "Action",
        start: "Start Over"
    },
    hindi: {
        profile: "मूल जानकारी",
        symptoms: "मुख्य लक्षण",
        pain: "दर्द की तीव्रता (1-10)",
        analyze: "विश्लेषण करें",
        assessment: "मूल्यांकन",
        condition: "संभावित स्थिति",
        risk: "जोखिम स्तर",
        action: "क्या करें",
        start: "फिर से शुरू करें"
    }
};

function setLanguage(lang){
    language = lang;

    document.getElementById("profileTitle").innerText = uiText[lang].profile;

    document.querySelector("h3:nth-of-type(2)").innerText = uiText[lang].symptoms;
    document.querySelector("h3:nth-of-type(3)").innerText = uiText[lang].pain;

    document.querySelector(".primary").innerText = uiText[lang].analyze;

    document.getElementById("languageCard").classList.add("hidden");
    document.getElementById("formCard").classList.remove("hidden");
}

function checkPregnancy(){
    let sex = document.getElementById("sex").value;
    if(sex === "Female"){
        document.getElementById("pregnancyDiv").classList.remove("hidden");
    } else {
        document.getElementById("pregnancyDiv").classList.add("hidden");
    }
}

function analyze(){

    let symptoms = Array.from(document.querySelectorAll(".symptom:checked")).map(x => x.value);

    fetch("/analyze",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
            language: language,
            age:document.getElementById("age").value || "",
            sex:document.getElementById("sex").value || "",
            pregnant:document.getElementById("pregnant")?.value || "",
            height:document.getElementById("height").value || "",
            weight:document.getElementById("weight").value || "",
            pain:document.getElementById("pain").value || "",
            symptoms:symptoms
        })
    })
    .then(res=>res.json())
    .then(data=>{
        showResult(data.condition, data.risk, data.action);
    })
    .catch(()=>{
        alert("Server error.");
    });
}

function showResult(condition,risk,action){

    document.getElementById("formCard").classList.add("hidden");

    let riskClass = "risk-low";
    if(risk==="Medium") riskClass="risk-medium";
    if(risk==="High") riskClass="risk-high";
    if(risk==="Emergency") riskClass="risk-emergency";

    document.getElementById("resultCard").innerHTML = `
        <h2>${uiText[language].assessment}</h2>
        <p><strong>${uiText[language].condition}:</strong> ${condition}</p>
        <p><strong>${uiText[language].risk}:</strong> <span class="${riskClass}">${risk}</span></p>
        <p><strong>${uiText[language].action}:</strong> ${action}</p>
        <button onclick="location.reload()">${uiText[language].start}</button>
    `;

    document.getElementById("resultCard").classList.remove("hidden");
}

</script>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json

    bmi = 0
    if data["height"] and data["weight"]:
        bmi = round(float(data["weight"]) / ((float(data["height"])/100)**2),1)

    if data.get("language") == "hindi":
        instruction = "Respond in Hindi."
    else:
        instruction = "Respond in English."

    prompt = f"""
You are a clinical triage AI.
{instruction}

AGE: {data.get("age")}
SEX: {data.get("sex")}
PREGNANT: {data.get("pregnant")}
BMI: {bmi}
PAIN SCALE: {data.get("pain")}
SYMPTOMS: {', '.join(data.get("symptoms", []))}

Respond strictly:

CONDITION: ...
RISK: Low / Medium / High
ACTION: ...
"""

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role":"user","content":prompt}]
    )

    text = response.choices[0].message.content

    condition = re.search(r"CONDITION:\s*(.*)",text)
    risk = re.search(r"RISK:\s*(.*)",text)
    action = re.search(r"ACTION:\s*(.*)",text)

    return jsonify({
        "condition": condition.group(1) if condition else "Unknown",
        "risk": risk.group(1) if risk else "Medium",
        "action": action.group(1) if action else "Consult doctor."
    })

if __name__ == "__main__":
    app.run()