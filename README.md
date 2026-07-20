# Job Delivery Dashboard — Setup Guide

Isme aapka Python Streamlit dashboard hai. Ek baar setup karne ke baad, aapko
ek permanent online link mil jayega jo UK/USA management ke saath share kar sakte hain.
Data update karne ke liye bas `update_dashboard.bat` double-click karna hoga.

---

## Folder mein kya hai

| File | Kaam |
|---|---|
| `dashboard.py` | Dashboard ka poora code |
| `data/Raw_Data.xlsx` | Aapka current data (isi file ko update karte rahenge) |
| `requirements.txt` | Python libraries jo dashboard ko chahiye |
| `update_dashboard.bat` | Ek-click data update + online publish |

---

## ONE-TIME SETUP (~15-20 minute, sirf ek baar karna hai)

### Step 1 — GitHub account banayein
1. https://github.com par jaake free account banayein (agar pehle se nahi hai).
2. https://desktop.github.com se **GitHub Desktop** install karein — isse aapko
   git commands yaad nahi rakhne padenge, sab click se ho jayega.

### Step 2 — Ek naya repository (repo) banayein
1. GitHub.com par login karke top-right "+" → **New repository** click karein.
2. Naam dein: `job-delivery-dashboard` (ya jo pasand ho).
3. **Private** ya **Public** — dono chalega (Private is safer agar company data hai).
4. "Create repository" click karein.

### Step 3 — Ye folder GitHub par upload karein
1. GitHub Desktop kholein → **File → Add Local Repository** → is poore folder
   (`streamlit_dashboard`) ko select karein.
2. Agar puche "create a repository here", to haan bol dein.
3. Left side mein **Publish repository** button dabayein, wahi repo naam select
   karein jo Step 2 mein banaya tha.
4. Ho gaya — aapka code ab GitHub par hai.

### Step 4 — Streamlit Community Cloud se connect karein
1. https://share.streamlit.io par jaake apne GitHub account se sign in karein.
2. **"Create app"** → **"Deploy a public app from GitHub"** select karein.
3. Repository: apni `job-delivery-dashboard` select karein.
4. Branch: `main`
5. Main file path: `dashboard.py`
6. **Deploy** dabayein — 1-2 minute mein aapka dashboard live ho jayega, aur
   aapko ek link milega jaisे: `https://your-app-name.streamlit.app`
7. **Yahi link UK/USA management ke saath share kar dijiye.** Jo bhi is link ko
   khole ga, use hamesha latest data ka dashboard dikhega — kisi login/setup ki
   zaroorat nahi.

---

## ROZANA DATA UPDATE (isi ke liye bat file hai)

1. `update_dashboard.bat` ko Notepad se ek baar kholein aur ye line edit karein:
   ```
   set SOURCE_FILE=C:\Users\YourName\Desktop\Raw_Data.xlsx
   ```
   Yahan apni us Excel file ka **poora path** likhein jise aap roz update karte hain
   (jaise apne Desktop par rakhi hui file). Save karke Notepad band kar dein.

2. Jab bhi naya data ready ho:
   - Us Excel file ko usi path par save karein (jo Step 1 mein set kiya).
   - `update_dashboard.bat` par **double-click** karein.
   - Ek black window khulegi, kuch second mein "Done!" dikhega.
   - 30-60 second wait karke apna online dashboard link browser mein refresh
     karein — naya data dikhega.

**Note:** Pehli baar bat file chalane se pehle, GitHub Desktop kholke apna naam/email
set karna padega (ye GitHub Desktop khud puch lega, ek baar ki setup hai). Agar bat
file "git not recognized" error de, to https://git-scm.com/download/win se Git install
kar lein (GitHub Desktop ke saath aata hai, par kabhi kabhi PATH mein add nahi hota).

---

## Agar kuch atka to

- **Dashboard blank/error dikhaye:** Excel file ke column headers check karein —
  kam se kam "Job No.", "Market", "Job Type" naam ke columns hone chahiye (extra
  spaces/case farq nahi padta, dashboard khud match kar leta hai).
- **Streamlit Cloud par "app has gone to sleep":** Free tier par agar app kuch
  din tak use na ho to so jata hai — link kholte hi 30 second mein khud jaag jata
  hai, kuch karne ki zaroorat nahi.
- **bat file "Could not find" error de:** SOURCE_FILE path galat hai — file ka
  sahi path check karke Notepad mein fix karein.
