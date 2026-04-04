# 🚀 Full Stack Deployment Guide

This guide provides the exact step-by-step process for deploying the **Fear-Free Night Navigator** across a split-stack infrastructure: hosting the React SPA on **Vercel** and the Python FastAPI / PostgreSQL database on **Render**.

---

## Part 1: Deploy the PostgreSQL Database (Render)

We start here because your backend needs a database URL to run successfully.

1. **Log in to Render** (https://dashboard.render.com).
2. Click the **"New +"** button in the top right.
3. Select **PostgreSQL**.
4. Fill in the required details:
   - **Name:** `safeway-db` (or anything you prefer)
   - **Database:** `safeway-db`
   - **User:** `safeway_admin`
   - **Instance Type:** Select the **Free** tier.
5. Click **Create Database**.
6. Immediately locate the **"Internal Database URL"** string on the screen and copy it. It looks like: 
   `postgresql://safeway_admin:password@dpg-c12345678/safeway`
   *(Keep this copied, we will need it for the Python backend).*

---

## Part 2: Deploy the Python Backend (Render)

Render will natively run your Python graph engine and apply the PostGIS extensions automatically.

1. In your Render Dashboard, click **New +** and select **Web Service**.
2. Connect your GitHub account and select your `SafeWay-Navigator` repository.
3. Fill in the Web Service configuration:
   - **Name:** `safeway-backend`
   - **Root Directory:** Type `backend` (very important!).
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt && python data/seed.py`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port 10000`
   - **Instance Type:** Free Tier.
4. Scroll down and click on **Advanced**.
5. Click **Add Environment Variable** and add the following keys:
   - **Key:** `DATABASE_URL`
     **Value:** *(Paste your Internal Database URL from Step 1)*
   - **Key:** `VITE_MAPBOX_TOKEN`
     **Value:** *(Paste your Mapbox token starting with pk.eyJ... This is essential for the backend's live traffic penalty engine)*
   - **Key:** `GOOGLE_PLACES_API_KEY` *(Optional)*
     **Value:** *(Paste your Google API key if you want real-time commercial "eyes on the street" activity)*
6. Click **Create Web Service**. 

> [!NOTE]
> The initial deployment may take 3-5 minutes as it downloads all mapping datasets and builds out the spatial Graph network via `seed.py`.

Once the deployment finishes and shows up as "Live", look at the top left of your screen and copy your new backend URL (e.g., `https://safeway-backend.onrender.com`).

---

## Part 3: Deploy the React Frontend (Vercel)

Now that your routing backend is live on the internet, we point the frontend to it!

1. **Log in to Vercel** (https://vercel.com/new).
2. Click **Add New Project**.
3. Import your `SafeWay-Navigator` GitHub repository.
4. Expand the **"Build and Output Settings"** section. Vercel should auto-detect Vite.
   - **Root Directory:** Click Edit and type `frontend`.
5. Expand the **"Environment Variables"** section and safely add the following:
   - **Key:** `VITE_MAPBOX_TOKEN`
     - **Value:** *(Paste your private Mapbox API key here)*
   - **Key:** `VITE_BACKEND_URL`
     - **Value:** *(Paste your Render backend URL from Part 2, without a trailing slash!)*
6. Click **Deploy**.

> [!IMPORTANT]
> The `vercel.json` file inside your repository will automatically configure the correct serverless routing paths so page reloads don't result in 404 errors.

---

### 🎉 Done!
After Vercel completes the build (usually takes ~30 seconds), click on your new production domain. The map will load and the routing engine will correctly trigger the AI A* routing logic hosted live on Render!
