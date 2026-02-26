from flask import Flask, request, jsonify, render_template_string
from groq import Groq
import os

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VAID Adaptive AI Triage</title>

<style>
body {
    margin:0;
    font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
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
.primary { background:#d63384; color:white; }
.secondary { background:#eee; }

input, select {
    width:100%;
    padding:12px;
    margin-top:8px;
    border-radius:10px;
    border:1px solid #ccc;
}
.checkbox-group {
    display:flex;
    align-items:center;
    gap:10px;
    margin-top:10px;
}
.checkbox-group input { width:auto; }

.hidden { display:none; }

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

    <h3 id="symptomTitle">Main Symptoms</h3>

    <div class="checkbox-group"><input type="checkbox" value="Fever" class="symptom"> Fever</div>
    <div class="checkbox-group"><input type="checkbox" value="Chest pain" class="symptom"> Chest pain</div>
    <div class="checkbox-group"><input type="checkbox" value="Shortness of breath" class="symptom"> Shortness of breath</div>
    <div class="checkbox-group"><input type="checkbox" value="Severe headache" class="symptom"> Severe headache</div>
    <div class="checkbox-group"><input type="checkbox" value="Heavy bleeding" class="symptom"> Heavy bleeding</div>
    <div class="checkbox-group"><input type="checkbox" value="Abdominal pain" class="symptom"> Abdominal pain</div>
    <div class="checkbox-group"><input type="checkbox" value="Vomiting" class="symptom"> Vomiting</div>

    <h3 id="painTitle">Pain Severity (1-10)</h3>
    <input type="number" id="pain" min="1" max="10">

    <button class="primary" onclick="analyze()" id="analyzeBtn">Analyze</button>

</div>

<div id="resultCard" class="card hidden"></div>
</div>

<script>

let language = "english";

const uiText = {
    english:{
        profile:"Basic Profile",
        symptoms:"Main Symptoms",
        pain:"Pain Severity (1-10)",
        analyze:"Analyze",
        assessment:"Assessment",
        condition:"Condition",
        risk:"Risk",
        action:"Action",
        start:"Start Over"
    },
    hindi:{
        profile:"मूल जानकारी",
        symptoms:"मुख्य लक्षण",
        pain:"दर्द की तीव्रता (1-10)",
        analyze:"विश्लेषण करें",
        assessment:"मूल्यांकन",
        condition:"संभावित स्थिति",
        risk:"जोखिम स्तर",
        action:"क्या करें",
        start:"फिर से शुरू करें"
    }
};

function setLanguage(lang){
    language = lang;
    document.getElementById("profileTitle").innerText = uiText[lang].profile;
    document.getElementById("symptomTitle").innerText = uiText[lang].symptoms;
    document.getElementById("painTitle").innerText = uiText[lang].pain;
    document.getElementById("analyzeBtn").innerText = uiText[lang].analyze;
    document.getElementById("languageCard").classList.add("hidden");
    document.getElementById("formCard").classList.remove("hidden");
}

function checkPregnancy(){
    let sex = document.getElementById("sex").value;
    document.getElementById("pregnancyDiv").classList.toggle("hidden", sex!=="Female");
}

function analyze(){

    let symptoms = Array.from(
        document.querySelectorAll(".symptom:checked")
    ).map(x=>x.value);

    fetch("/analyze",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
            language:language,
            age:age.value||"",
            sex:sex.value||"",
            pregnant:pregnant?.value||"",
            height:height.value||"",
            weight:weight.value||"",
            pain:pain.value||"",
            symptoms:symptoms
        })
    })
    .then(res=>res.json())
    .then(data=>{
        if(data.error){ alert(data.error); return; }
        showResult(data.condition,data.risk,data.action);
    })
    .catch(()=>alert("Network error"));
}

function showResult(condition,risk,action){

    let riskClass="risk-low";
    if(risk==="Medium") riskClass="risk-medium";
    if(risk==="High") riskClass="risk-high";
    if(risk==="Emergency") riskClass="risk-emergency";

    resultCard.innerHTML=`
        <h2>${uiText[language].assessment}</h2>
        <p><strong>${uiText[language].condition}:</strong> ${condition}</p>
        <p><strong>${uiText[language].risk}:</strong> <span class="${riskClass}">${risk}</span></p>
        <p><strong>${uiText[language].action}:</strong> ${action}</p>
        <button onclick="location.reload()">${uiText[language].start}</button>
    `;

    formCard.classList.add("hidden");
    resultCard.classList.remove("hidden");
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
    try:
        data = request.json
        language = data.get("language","english")
        symptoms = ", ".join(data.get("symptoms",[]))

        prompt=f"""
Age:{data.get('age')}
Sex:{data.get('sex')}
Pregnant:{data.get('pregnant')}
Height:{data.get('height')}
Weight:{data.get('weight')}
Pain:{data.get('pain')}
Symptoms:{symptoms}

Give:
1. Likely condition
2. Risk (Low/Medium/High/Emergency)
3. Recommended action
"""

        if language=="hindi":
            prompt+="\nRespond fully in Hindi."

        client=Groq(api_key=os.environ.get("GROQ_API_KEY"))

        response=client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role":"user","content":prompt}]
        )

        text=response.choices[0].message.content

        return jsonify({
            "condition":text,
            "risk":"Medium",
            "action":"Consult a doctor if symptoms persist."
        })

    except Exception as e:
        return jsonify({"error":str(e)}),500


if __name__=="__main__":
    app.run(host="0.0.0.0", port=10000)