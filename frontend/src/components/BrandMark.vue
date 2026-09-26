<script setup lang="ts">
withDefaults(defineProps<{ compact?: boolean }>(), { compact: false })
</script>

<template>
  <span class="rovia-brand" aria-label="Rovia">
    <img src="/rovia-mark.svg" width="40" height="40" alt="" />
    <span><strong>Rovia</strong><small v-if="!compact">把远方排进日常</small></span>
  </span>
</template>
