import { readFileSync, writeFileSync } from 'node:fs'

const databaseId = process.env.CLOUDFLARE_D1_DATABASE_ID
if (!databaseId) {
  throw new Error('CLOUDFLARE_D1_DATABASE_ID is required for a production D1 deployment')
}

const config = JSON.parse(readFileSync(new URL('../wrangler.jsonc', import.meta.url), 'utf8'))
config.d1_databases[0].database_id = databaseId
writeFileSync('.wrangler.deploy.jsonc', `${JSON.stringify(config, null, 2)}\n`)
console.log('Prepared .wrangler.deploy.jsonc for D1 database:', databaseId)
