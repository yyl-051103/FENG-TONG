<script setup lang="ts">
import { onMounted } from "vue";
import { useUserStore } from "./stores/user";

const store = useUserStore();

onMounted(() => {
  if (store.isLoggedIn) {
    store.fetchUserInfo();
  }
});
</script>

<template>
  <router-view />
</template>

<style>
:root {
  --primary: #2196f3;
  --primary-light: #64b5f6;
  --primary-dark: #1976d2;
  --primary-bg: #e3f5fd;
  --surface: #ffffff;
  --text-primary: #1a237e;
  --text-secondary: #546e7a;
  --text-muted: #90a4ae;
  --border: #e1f5fe;
  --shadow: 0 4px 20px rgba(33,150,243,0.12);
  --shadow-hover: 0 8px 32px rgba(33,150,243,0.2);
  --radius: 16px;
  --radius-sm: 12px;
}
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: linear-gradient(180deg, #f0f7ff 0%, #e8f4fd 100%);
  min-height: 100vh;
  color: var(--text-primary);
}
</style>
