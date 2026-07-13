<script setup lang="ts">
import { onMounted } from 'vue'

onMounted(() => {
  if ('serviceWorker' in navigator) {
    import('virtual:pwa-register')
      .then(({ registerSW }) => {
        registerSW({ immediate: true })
      })
      .catch(() => {
        /* ignore when PWA plugin unavailable */
      })
  }
})
</script>

<template>
  <div class="app-shell">
    <router-view />
  </div>
</template>
