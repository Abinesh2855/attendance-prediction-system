# Attendance AI — Step 1

Modern Flask attendance dashboard using the supplied July–September 2026 Excel dataset.

## Run in VS Code / PowerShell

```powershell
python -m venv venv
.env\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## Step 1 features
- Excel dataset loading
- Summary cards
- Daily attendance trend
- Present/Absent doughnut chart
- Monthly attendance chart
- Student attendance chart
- Student detail panel
- Baseline prediction preview

## Important
The `/api/predict` endpoint is deliberately a baseline probability estimate. It is **not yet the final ML model**. Step 3 will replace it with a trained classification model and evaluation metrics.
