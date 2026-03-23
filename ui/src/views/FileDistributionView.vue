<template>
  <n-space vertical :size="24">
    <n-card class="home-hero" :bordered="false" embedded>
      <n-space vertical :size="12">
        <n-h1 class="home-view__heading">Распределение файлов</n-h1>
        <n-p depth="2" class="home-view__lead">
          Здесь позже появится инструмент для разнесения файлов по папкам или правилам. Пока раздел пустой.
        </n-p>
      </n-space>
    </n-card>

    <n-card :bordered="true" class="file-distribution-placeholder">
      <n-empty description="Контент в разработке" />
    </n-card>
  </n-space>
</template>

<script setup lang="ts">
</script>
