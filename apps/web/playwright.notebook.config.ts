import { defineConfig, devices } from '@playwright/test';
export default defineConfig({
 testDir:'./tests/e2e',testMatch:'review-notebook.home.ts',workers:1,fullyParallel:false,
 timeout:30_000,expect:{timeout:10_000},
 reporter:[['list'],['html',{outputFolder:'playwright-notebook-report',open:'never'}]],outputDir:'test-results/notebook',
 use:{baseURL:'http://127.0.0.1:13009',trace:'retain-on-failure',screenshot:'only-on-failure'},
 projects:[
  {name:'desktop',use:{...devices['Desktop Chrome'],viewport:{width:1440,height:1000}}},
  {name:'mobile',use:{...devices['Desktop Chrome'],viewport:{width:390,height:844},isMobile:true,hasTouch:true}},
  {name:'mobile-webkit',use:{...devices['iPhone 13'],viewport:{width:390,height:844}}},
 ],
 webServer:[
  {command:'node tests/e2e/review-notebook-api.mjs',url:'http://127.0.0.1:18770/__health',reuseExistingServer:false},
  {command:'npm run start -- -p 13009',url:'http://127.0.0.1:13009/stocks/AAPL/review',reuseExistingServer:false,
   env:{STOCKANALYSIS_FRONTEND_API_BASE_URL:'http://127.0.0.1:18770',STOCKANALYSIS_FRONTEND_API_READ_TOKEN:'notebook-fixture-only',NEXT_TELEMETRY_DISABLED:'1'}},
 ],
});
