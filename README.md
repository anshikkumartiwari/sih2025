# Compliance Checker Project

## how to run (windows)
1. **Create a folder and clone**

```
git clone https://github.com/anshikkumartiwari/sih2025.git
cd sih2025
```

2. **Create & activate virtual environment**

```
python -m venv .venv
.venv\Scripts\Activate
```

3. **Install dependencies**

```
pip install -r requirements.txt
```

4. **Run the app**

```
python app.py
```

5. **Open in browser**
   [http://127.0.0.1:5000](http://127.0.0.1:5000)






## Directory Tree
```
sih2025
├─ 📁core
│  ├─ 📁crawlers
│  │  └─ 📄amazon.py
│  ├─ 📄master.py
│  ├─ 📄ocr.py
│  ├─ 📄rules.py
│  ├─ 📄vision.py
│  └─ 📄__init__.py
├─ 📁dashboard
│  ├─ 📁static
│  │  ├─ 📁css
│  │  │  └─ 📄style.css
│  │  ├─ 📁img
│  │  │  └─ 📄placeholder.png
│  │  └─ 📁js
│  │     └─ 📄dashboard.js
│  ├─ 📁templates
│  │  ├─ 📄index.html
│  │  ├─ 📄process.html
│  │  └─ 📄report.html
│  ├─ 📄dashboard.py
│  └─ 📄__init__.py
├─ 📁temp
├─ 📄.gitignore
├─ 📄app.py
├─ 📄README.md
└─ 📄requirements.txt
```