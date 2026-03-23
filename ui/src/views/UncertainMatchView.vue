<template>
  <AppPage title="Совпадение под вопросом" variant="uncertain">
    <template v-if="payload" #headerExtra>
      <UncertainPairMeta
        :pair-key="payload.key"
        :item="payload.item"
        :unprocessed-pair-count="payload.unprocessed_pair_count"
      />
    </template>

    <UncertainFetchState
      :loading="loading"
      :error-message="errorMessage"
      @retry="loadFirstNotProcessed"
    >
      <UncertainPairContent
        v-if="payload"
        :payload="payload"
        :previews-loading="previewsLoading"
        :preview-error="previewError"
        :left-image-url="leftImageUrl"
        :right-image-url="rightImageUrl"
        :path-copied-side="pathCopiedSide"
        @copy-path="onCopyPath"
        @resolved="loadFirstNotProcessed"
      />
    </UncertainFetchState>
  </AppPage>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import AppPage from "../components/AppPage.vue";
import UncertainFetchState from "../components/uncertain/UncertainFetchState.vue";
import UncertainPairContent from "../components/uncertain/UncertainPairContent.vue";
import UncertainPairMeta from "../components/uncertain/UncertainPairMeta.vue";
import {
  fetchFirstNotProcessedNearDuplicate,
  NearDuplicatesRequestError,
} from "../api/nearDuplicates";
import { usePathCopy } from "../composables/usePathCopy";
import { fetchMediaBlob } from "../api/media";
import type {
  FirstNotProcessedNearDuplicateResponse,
  NearDuplicatePairItem,
} from "../types/nearDuplicates";

const { pathCopiedSide, copyFilePath } = usePathCopy();

const loading = ref(true);
const errorMessage = ref<string | null>(null);
const payload = ref<FirstNotProcessedNearDuplicateResponse | null>(null);

const previewsLoading = ref(false);
const previewError = ref<string | null>(null);
const leftImageUrl = ref<string | null>(null);
const rightImageUrl = ref<string | null>(null);

function onCopyPath(side: "left" | "right", path: string | undefined): void {
  void copyFilePath(side, path);
}

function revokePreviewUrls(): void {
  if (leftImageUrl.value?.startsWith("blob:")) {
    URL.revokeObjectURL(leftImageUrl.value);
  }
  if (rightImageUrl.value?.startsWith("blob:")) {
    URL.revokeObjectURL(rightImageUrl.value);
  }
  leftImageUrl.value = null;
  rightImageUrl.value = null;
}

async function loadPreviewImages(item: NearDuplicatePairItem): Promise<void> {
  revokePreviewUrls();
  previewError.value = null;

  const leftId = item.left.file_id?.trim();
  const rightId = item.right.file_id?.trim();

  if (!leftId || !rightId) {
    previewError.value =
      "Нет file_id у одной из сторон. Пересобери индекс и отчёт: scan_files_to_json.py и analyze_duplicates.py.";
    return;
  }

  previewsLoading.value = true;
  try {
    const [leftBlob, rightBlob] = await Promise.all([
      fetchMediaBlob(leftId),
      fetchMediaBlob(rightId),
    ]);
    leftImageUrl.value = URL.createObjectURL(leftBlob);
    rightImageUrl.value = URL.createObjectURL(rightBlob);
  } catch (e) {
    previewError.value =
      e instanceof Error ? e.message : "Не удалось загрузить превью файлов";
  } finally {
    previewsLoading.value = false;
  }
}

async function loadFirstNotProcessed(): Promise<void> {
  loading.value = true;
  errorMessage.value = null;
  payload.value = null;
  revokePreviewUrls();
  previewError.value = null;

  try {
    const data = await fetchFirstNotProcessedNearDuplicate();
    payload.value = data;
    await loadPreviewImages(data.item);
  } catch (e) {
    if (e instanceof NearDuplicatesRequestError) {
      errorMessage.value = e.message;
    } else if (e instanceof Error) {
      errorMessage.value = e.message;
    } else {
      errorMessage.value = "Неизвестная ошибка";
    }
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  void loadFirstNotProcessed();
});

onBeforeUnmount(() => {
  revokePreviewUrls();
});
</script>
