# Cloudflare Deployment

The current Compose stack is for local development. It is not a single Cloudflare deployment unit.

## Recommended production split

1. Deploy `frontend/` to Cloudflare Pages.
   - Build command: `npm run build`
   - Output directory: `dist`
   - Set `VITE_API_BASE_URL=https://api.example.com` if the API uses a separate hostname.
2. Deploy the FastAPI image to a persistent container host or Cloudflare Containers.
3. Use a managed MySQL instance. If the API is moved to a Worker, Cloudflare Hyperdrive can connect the Worker to an external MySQL database.
4. Use a managed MQTT provider or a secured Mosquitto host. Do not expose the local anonymous Mosquitto configuration publicly.
5. Set `CORS_ORIGINS` to the exact Pages/custom-domain origin.

## Pages GitHub Actions

The repository includes `.github/workflows/deploy-pages.yml`. Configure these GitHub repository values before enabling it:

- Secret `CLOUDFLARE_API_TOKEN`: token with Pages Write permission.
- Secret `CLOUDFLARE_ACCOUNT_ID`: Cloudflare account ID.
- Variable `CLOUDFLARE_PAGES_PROJECT`: Pages project name.
- Variable `VITE_API_BASE_URL`: public API origin, for example `https://api.example.com`.

The workflow runs on pushes to `master` that change `frontend/` and uses `npm install` followed by `npm run build`. Commit a generated `package-lock.json` later if reproducible dependency locking is required.

## Production environment variables

```text
DATABASE_URL=mysql+pymysql://...
MQTT_HOST=...
MQTT_PORT=8883
MQTT_USERNAME=...
MQTT_PASSWORD=...
MQTT_TLS=true
CORS_ORIGINS=https://app.example.com
```

The application keeps the MQTT, database, and frontend contracts unchanged across local and production deployments.
