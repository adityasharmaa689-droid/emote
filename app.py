import os
import json
import logging
import requests
from io import BytesIO
from flask import Flask, jsonify, send_file, Response, request

# --- Logging setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- File paths ---
ITEM_DATA_PATH = "itemData.json"
GITHUB_EMOTE_BASE = "https://raw.githubusercontent.com/adityasharmaa689-droid/emote/main/emote/"

# --- Load item data ---
def load_item_data():
    try:
        with open(ITEM_DATA_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading item data: {e}")
        return []

# --- HTML Page ---
HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Emote Library</title>
<style>
body {
  font-family: 'Poppins', sans-serif;
  background: radial-gradient(circle at top left, #0f0f0f, #1a1a1a);
  color: #f0f0f0;
  margin: 0;
  overflow-x: hidden;
}
header {
  background: #181818;
  padding: 14px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 12px rgba(0,0,0,0.5);
}
header h1 {
  font-size: 22px;
  margin: 0;
  color: #fff;
  font-weight: 600;
}
.dropdown {
  position: relative;
}
.dropdown button {
  background: #2a2a2a;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s ease;
}
.dropdown button:hover {
  background: #383838;
  transform: scale(1.05);
}
.dropdown-content {
  display: none;
  position: absolute;
  right: 0;
  background-color: #1b1b1b;
  min-width: 120px;
  border-radius: 8px;
  box-shadow: 0 8px 16px rgba(0,0,0,0.4);
  overflow-y: auto;
  max-height: 260px;
  animation: dropdownFade 0.3s ease;
}
@keyframes dropdownFade {
  from {opacity: 0; transform: translateY(-8px);}
  to {opacity: 1; transform: translateY(0);}
}
.dropdown-content button {
  background: none;
  color: #fff;
  border: none;
  padding: 10px 14px;
  text-align: left;
  width: 100%;
  cursor: pointer;
}
.dropdown-content button:hover {
  background-color: #333;
}

.container {
  padding: 15px;
}
.filters {
  display: flex;
  justify-content: center;
  margin-bottom: 15px;
}
.filters input {
  width: 90%;
  max-width: 420px;
  padding: 10px 14px;
  border-radius: 8px;
  border: none;
  background: #252525;
  color: white;
  outline: none;
  font-size: 15px;
}
.grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  max-height: calc(100vh - 250px);
  overflow-y: auto;
  scroll-behavior: smooth;
  padding-right: 6px;
}
.grid::-webkit-scrollbar {
  width: 6px;
}
.grid::-webkit-scrollbar-thumb {
  background: #444;
  border-radius: 4px;
}
.card {
  background: #1a1a1a;
  border-radius: 10px;
  padding: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  transition: transform 0.25s ease, background 0.25s ease;
  cursor: pointer;
  animation: fadeIn 0.4s ease;
}
.card:hover {
  background: #2b2b2b;
  transform: scale(1.06);
}
.card img {
  max-width: 90%;
  border-radius: 8px;
  box-shadow: 0 0 8px rgba(0,0,0,0.5);
}
.tooltip {
  font-size: 12px;
  color: #aaa;
  margin-top: 5px;
}

/* Pagination */
.pagination {
  text-align: center;
  margin-top: 18px;
}
.pagination button {
  background: #272727;
  color: white;
  border: none;
  padding: 8px 14px;
  margin: 0 3px;
  border-radius: 6px;
  cursor: pointer;
  transition: 0.2s;
}
.pagination button.active {
  background: #4b4b4b;
}
.pagination button:hover {
  background: #3a3a3a;
}

.modal {
  display:none;
  position:fixed;
  top:0; left:0;
  width:100%; height:100%;
  background:rgba(0,0,0,0.9);
  justify-content:center;
  align-items:center;
  z-index:200;
}
.modal-content {
  background:#1e1e1e;
  padding:20px;
  border-radius:10px;
  max-width:420px;
  width:90%;
  text-align:center;
}
.modal-content img {
  max-width:100%;
  border-radius:8px;
  margin-bottom: 10px;
}
.close {
  position:absolute;
  top:10px;
  right:20px;
  color:white;
  font-size:22px;
  cursor:pointer;
}
</style>
</head>
<body>
<header>
  <h1>Emote Library</h1>
  <div class="dropdown">
    <button onclick="toggleDropdown()">OB Update ▼</button>
    <div id="obDropdown" class="dropdown-content"></div>
  </div>
</header>

<div class="container">
  <div class="filters">
    <input type="text" id="searchBox" placeholder="Search by Name, ID, or OB Code (e.g. OB48, 909048)">
  </div>
  <div id="itemsGrid" class="grid"></div>
  <div class="pagination" id="pagination"></div>
</div>

<div id="itemModal" class="modal">
  <div class="modal-content">
    <span class="close">&times;</span>
    <img id="modalIcon" src="">
    <h2 id="modalName"></h2>
    <p id="modalId"></p>
    <p id="modalDesc"></p>
  </div>
</div>

<script>
const FALLBACK_IMG = "https://via.placeholder.com/100/333333/FFFFFF?text=No+Image";
let allItems = [], selectedOB = "all", currentPage = 1, itemsPerPage = 100;

async function fetchData() {
  const res = await fetch("/item-data");
  allItems = await res.json();
  createOBDropdown();
  renderItems();
}
function createOBDropdown(){
  const dropdown = document.getElementById("obDropdown");
  dropdown.innerHTML = "";
  const allBtn = document.createElement("button");
  allBtn.textContent = "All";
  allBtn.onclick = ()=>selectOB("all");
  dropdown.appendChild(allBtn);
  for(let i=33; i<=51; i++){
    const code = "OB" + i;
    const btn = document.createElement("button");
    btn.textContent = code;
    btn.onclick = ()=>selectOB(code);
    dropdown.appendChild(btn);
  }
}
function toggleDropdown(){
  const d = document.getElementById("obDropdown");
  d.style.display = d.style.display === "block" ? "none" : "block";
}
window.onclick = e => {
  if (!e.target.matches('.dropdown button')) {
    document.getElementById("obDropdown").style.display = "none";
  }
}
function selectOB(obCode){
  selectedOB = obCode;
  document.querySelector(".dropdown button").textContent = (obCode === "all" ? "OB Update ▼" : obCode + " ▼");
  currentPage = 1;
  renderItems();
}
function detectOB(search){
  const match1 = search.match(/9090(\\d{2})/);
  const match2 = search.match(/OB(\\d{2})/i);
  if (match1) return "OB" + match1[1];
  if (match2) return "OB" + match2[1];
  return null;
}
function applyFilters(){
  const search = document.getElementById("searchBox").value.toLowerCase().trim();
  const detectedOB = detectOB(search);
  const obCode = detectedOB || (selectedOB !== "all" ? selectedOB : null);
  return allItems.filter(i=>{
    const idStr = i.Id?.toString() || "";
    const matchesOB = obCode ? idStr.startsWith("9090" + obCode.replace("OB","")) : true;
    const matchesSearch = !search ||
        i.name?.toLowerCase().includes(search) ||
        idStr.includes(search);
    return matchesOB && matchesSearch;
  });
}
function renderItems(){
  const filtered = applyFilters();
  const grid = document.getElementById("itemsGrid");
  grid.innerHTML = "";
  const start = (currentPage - 1) * itemsPerPage;
  const end = start + itemsPerPage;
  const items = filtered.slice(start, end);
  items.forEach(item=>{
    const div = document.createElement("div");
    div.className = "card";
    div.innerHTML = `<img src="/image?itemid=${item.Id}" onerror="this.src='${FALLBACK_IMG}'">
                     <div class='tooltip'>${item.Id}</div>`;
    div.onclick = ()=>showDetails(item);
    grid.appendChild(div);
  });
  updatePagination(filtered.length);
}
function updatePagination(totalItems){
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const pagDiv = document.getElementById("pagination");
  pagDiv.innerHTML = "";
  for(let i=1; i<=totalPages; i++){
    const btn = document.createElement("button");
    btn.textContent = i;
    if(i === currentPage) btn.classList.add("active");
    btn.onclick = ()=>{currentPage=i;renderItems();};
    pagDiv.appendChild(btn);
  }
}
function showDetails(item){
  document.getElementById("modalIcon").src = `/image?itemid=${item.Id}`;
  document.getElementById("modalName").textContent = item.name || "Unknown";
  document.getElementById("modalId").textContent = "ID: " + item.Id;
  document.getElementById("modalDesc").textContent = item.desc || "No description available.";
  document.getElementById("itemModal").style.display = "flex";
}
document.querySelector(".close").onclick = ()=>document.getElementById("itemModal").style.display="none";
window.onclick = e=>{if(e.target==document.getElementById("itemModal"))document.getElementById("itemModal").style.display="none";}
document.getElementById("searchBox").addEventListener("input",()=>{currentPage=1;renderItems();});
fetchData();
</script>
</body>
</html>"""

# --- Flask app ---
app = Flask(__name__)

@app.route('/')
def index():
    return Response(HTML_PAGE, mimetype='text/html')

@app.route('/item-data')
def get_item_data():
    return jsonify(load_item_data())

@app.route('/image')
def get_image():
    itemid = request.args.get('itemid')
    if not itemid:
        return Response("Missing itemid", status=400)

    github_url = f"{GITHUB_EMOTE_BASE}{itemid}.png"
    try:
        resp = requests.get(github_url, timeout=5)
        if resp.status_code == 200 and resp.headers.get("Content-Type", "").startswith("image"):
            return send_file(BytesIO(resp.content), mimetype='image/png')
        else:
            return Response(status=404)
    except Exception as e:
        logger.error(f"GitHub fetch failed for {itemid}: {e}")
        return Response(status=404)

# --- Run app ---
if __name__ == "__main__":
    print("🚀 Server running on http://127.0.0.1:8000")
    app.run(host="0.0.0.0", port=8000, debug=False)
