<template>
  <n-space vertical :size="16" class="uncertain-pair">
    <div class="uncertain-pair__primary-actions">
      <n-space
        vertical
        :size="8"
        align="center"
        class="uncertain-choice-actions"
      >
        <n-space justify="center" wrap :size="12">
          <n-button
            type="warning"
            size="medium"
            :disabled="!selectedSide || submitting || !payload.item.uid"
            :loading="submitting"
            @click="onConfirmDeleteSide"
          >
            Удалить выбранный
          </n-button>
          <n-button
            type="error"
            size="medium"
            :disabled="submitting || !payload.item.uid"
            :loading="submitting"
            @click="onDeleteBoth"
          >
            Удалить оба
          </n-button>
          <n-button
            type="default"
            size="medium"
            :disabled="submitting || !payload.item.uid"
            :loading="submitting"
            @click="onKeepBoth"
          >
            Оставить оба
          </n-button>
        </n-space>
        <n-alert
          v-if="resolveError"
          type="error"
          :show-icon="true"
          class="uncertain-choice-actions__error"
        >
          {{ resolveError }}
        </n-alert>
      </n-space>
    </div>

    <n-divider dashed />

    <UncertainPreviewGrid
      :loading="previewsLoading"
      :error="previewError"
      :left-image-url="leftImageUrl"
      :right-image-url="rightImageUrl"
      :left="payload.item.left"
      :right="payload.item.right"
      :selected-side="selectedSide"
      @select-side="selectedSide = $event"
    />

    <n-grid
      cols="1 s:2"
      :x-gap="12"
      :y-gap="12"
      responsive="screen"
      class="uncertain-files-grid"
    >
      <n-gi>
        <UncertainFileDetailCard
          side="left"
          :file="payload.item.left"
          :path-copied="pathCopiedSide === 'left'"
          @copy-path="(p) => emit('copy-path', 'left', p)"
        />
      </n-gi>
      <n-gi>
        <UncertainFileDetailCard
          side="right"
          :file="payload.item.right"
          :path-copied="pathCopiedSide === 'right'"
          @copy-path="(p) => emit('copy-path', 'right', p)"
        />
      </n-gi>
    </n-grid>
  </n-space>
</template>

<script setup lang="ts">
import { useMessage } from "naive-ui";
import { ref, watch } from "vue";
import {
  NearDuplicatesRequestError,
  submitResolveNearDuplicateChoice,
} from "../../api/nearDuplicates";
import type { PathCopySide } from "../../composables/usePathCopy";
import type { FirstNotProcessedNearDuplicateResponse } from "../../types/nearDuplicates";
import UncertainFileDetailCard from "./UncertainFileDetailCard.vue";
import UncertainPreviewGrid from "./UncertainPreviewGrid.vue";

const props = defineProps<{
  payload: FirstNotProcessedNearDuplicateResponse;
  previewsLoading: boolean;
  previewError: string | null;
  leftImageUrl: string | null;
  rightImageUrl: string | null;
  pathCopiedSide: PathCopySide | null;
}>();

const emit = defineEmits<{
  "copy-path": [side: PathCopySide, path: string | undefined];
  resolved: [];
}>();

const selectedSide = ref<PathCopySide | null>(null);
const submitting = ref(false);
const resolveError = ref<string | null>(null);

function pairIdentity(p: FirstNotProcessedNearDuplicateResponse): string {
  const u = p.item.uid;
  if (u) return u;
  return `${p.item.left.file_id ?? ""}|${p.item.right.file_id ?? ""}|${p.key}`;
}

watch(
  () => pairIdentity(props.payload),
  () => {
    selectedSide.value = null;
    resolveError.value = null;
  },
);

const message = useMessage();

async function submitResolution(
  body: Parameters<typeof submitResolveNearDuplicateChoice>[0],
): Promise<void> {
  const uid = props.payload.item.uid?.trim();
  if (!uid) {
    resolveError.value =
      "У пары нет uid — пересобери duplicates-list.json (analyze_duplicates.py).";
    return;
  }

  resolveError.value = null;
  submitting.value = true;
  try {
    await submitResolveNearDuplicateChoice(body);
    message.success("Решение сохранено");
    emit("resolved");
  } catch (e) {
    const text =
      e instanceof NearDuplicatesRequestError
        ? e.message
        : e instanceof Error
          ? e.message
          : "Не удалось сохранить решение";
    resolveError.value = text;
    message.error(text);
  } finally {
    submitting.value = false;
  }
}

async function onConfirmDeleteSide(): Promise<void> {
  if (!selectedSide.value) return;
  const { key } = props.payload;
  const uid = props.payload.item.uid?.trim();
  if (!uid) return;
  await submitResolution({
    pair_uid: uid,
    key,
    chosen_side: selectedSide.value,
  });
}

async function onKeepBoth(): Promise<void> {
  const { key } = props.payload;
  const uid = props.payload.item.uid?.trim();
  if (!uid) return;
  await submitResolution({
    pair_uid: uid,
    key,
    keep_both: true,
  });
}

async function onDeleteBoth(): Promise<void> {
  const { key } = props.payload;
  const uid = props.payload.item.uid?.trim();
  if (!uid) return;
  await submitResolution({
    pair_uid: uid,
    key,
    delete_both: true,
  });
}
</script>
