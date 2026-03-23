<template>
  <n-space vertical :size="12">
    <n-p class="uncertain-view__p">
      <n-text>Сюда попадают пары и группы, которые </n-text>
      <n-text type="warning" strong>похожи, но не доказано</n-text>
      <n-text>
        , что это один и тот же файл: другое разрешение, перекодирование, чуть сдвинутый кадр, серия снимков с одной
        сцены.
      </n-text>
    </n-p>
    <n-p depth="3" class="uncertain-view__p--muted">
      Рекомендуется просматривать превью и решать вручную: оставить оба, объединить в одну группу или пометить как не
      дубликаты.
    </n-p>
  </n-space>
</template>
