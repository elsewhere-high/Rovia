<script setup lang="ts">
import BrandMark from '../components/BrandMark.vue'
</script>

<template>
  <main class="not-found-page">
    <BrandMark />
    <span class="eyebrow">404 · 路口之外</span>
    <h1>这条路还没有行程。</h1>
    <p>地址可能已经变更，回到工作台继续规划。</p>
    <RouterLink to="/home" class="primary-button">返回旅行工作台</RouterLink>
  </main>
</template>
