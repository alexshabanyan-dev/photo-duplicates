<template>
  <n-space vertical :size="12" class="uncertain-previews">
    <n-space
      v-if="loading"
      vertical
      :size="8"
      align="center"
      justify="center"
      class="uncertain-previews__loading"
    >
      <n-spin size="medium" />
      <n-text depth="3">Загрузка превью…</n-text>
    </n-space>

    <n-alert
      v-else-if="error"
      type="warning"
      :show-icon="true"
      :bordered="true"
      role="alert"
    >
      {{ error }}
    </n-alert>

    <n-grid v-else cols="1 s:2" :x-gap="12" :y-gap="12" responsive="screen" class="uncertain-previews__grid">
      <n-gi>
        <n-card
          size="small"
          :bordered="true"
          class="media-preview-card uncertain-file-card uncertain-preview-column"
          :class="{ 'uncertain-preview-column--selected': selectedSide === 'left' }"
        >
          <n-space vertical :size="10">
            <n-button
              block
              :type="selectedSide === 'left' ? 'warning' : 'default'"
              :secondary="selectedSide !== 'left'"
              @click="emit('select-side', 'left')"
            >
              {{ selectedSide === 'left' ? 'К удалению: левая' : 'Пометить левую к удалению' }}
            </n-button>
            <n-text
              v-if="left.path"
              depth="3"
              class="uncertain-file__path uncertain-preview__path"
            >
              {{ left.path }}
            </n-text>
            <div class="uncertain-preview__media" @click.stop>
              <template v-if="leftImageUrl">
                <video
                  v-if="isVideoFilename(left.filename ?? left.path)"
                  class="uncertain-preview__video"
                  controls
                  playsinline
                  preload="metadata"
                  :src="leftImageUrl"
                />
                <n-image
                  v-else
                  class="uncertain-preview__image"
                  :src="leftImageUrl"
                  object-fit="contain"
                  :alt="left.filename ?? 'Левый файл'"
                />
              </template>
            </div>
            <n-space vertical :size="6">
              <n-text strong class="uncertain-file__name">{{ left.filename ?? 'left' }}</n-text>
              <n-code v-if="left.file_id" class="uncertain-file__code">{{ left.file_id }}</n-code>
              <n-text v-else depth="3" italic>нет file_id</n-text>
            </n-space>
          </n-space>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card
          size="small"
          :bordered="true"
          class="media-preview-card uncertain-file-card uncertain-preview-column"
          :class="{ 'uncertain-preview-column--selected': selectedSide === 'right' }"
        >
          <n-space vertical :size="10">
            <n-button
              block
              :type="selectedSide === 'right' ? 'warning' : 'default'"
              :secondary="selectedSide !== 'right'"
              @click="emit('select-side', 'right')"
            >
              {{ selectedSide === 'right' ? 'К удалению: правая' : 'Пометить правую к удалению' }}
            </n-button>
            <n-text
              v-if="right.path"
              depth="3"
              class="uncertain-file__path uncertain-preview__path"
            >
              {{ right.path }}
            </n-text>
            <div class="uncertain-preview__media" @click.stop>
              <template v-if="rightImageUrl">
                <video
                  v-if="isVideoFilename(right.filename ?? right.path)"
                  class="uncertain-preview__video"
                  controls
                  playsinline
                  preload="metadata"
                  :src="rightImageUrl"
                />
                <n-image
                  v-else
                  class="uncertain-preview__image"
                  :src="rightImageUrl"
                  object-fit="contain"
                  :alt="right.filename ?? 'Правый файл'"
                />
              </template>
            </div>
            <n-space vertical :size="6">
              <n-text strong class="uncertain-file__name">{{ right.filename ?? 'right' }}</n-text>
              <n-code v-if="right.file_id" class="uncertain-file__code">{{ right.file_id }}</n-code>
              <n-text v-else depth="3" italic>нет file_id</n-text>
            </n-space>
          </n-space>
        </n-card>
      </n-gi>
    </n-grid>
  </n-space>
</template>

<script setup lang="ts">
import type { PathCopySide } from '../../composables/usePathCopy'
import type { NearDuplicateSide } from '../../types/nearDuplicates'
import { isVideoFilename } from '../../utils/mediaKind'

defineProps<{
  loading: boolean
  error: string | null
  leftImageUrl: string | null
  rightImageUrl: string | null
  left: NearDuplicateSide
  right: NearDuplicateSide
  selectedSide: PathCopySide | null
}>()

const emit = defineEmits<{
  'select-side': [side: PathCopySide]
}>()
</script>
