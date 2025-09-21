import { defineConfig } from 'cypress';

export default defineConfig({
  e2e: {
    baseUrl: 'https://platform.mapmystandards.ai',
    video: false,
    supportFile: false,
    defaultCommandTimeout: 10000,
    retries: 1,
  },
});
