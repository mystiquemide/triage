<template>
  <span
    :class="{
      'text-yellow-400 bg-yellow-900 bg-opacity-30': st === 'pending',
      'text-green-400 bg-green-900 bg-opacity-30': st === 'accepted',
      'text-red-400 bg-red-900 bg-opacity-30': st === 'rejected',
      'text-purple-400 bg-purple-900 bg-opacity-30': st === 'duplicate',
      'text-gray-400 bg-gray-700': !st,
    }"
    class="px-2 py-0.5 rounded text-xs font-medium"
  >
    {{ label }}
  </span>
</template>

<script setup>
import { computed } from "vue";
const props = defineProps({ status: String });
const st = computed(() => (props.status || "").toLowerCase());
const label = computed(() => {
  const map = { pending: "Pending", accepted: "Accepted", rejected: "Rejected", duplicate: "Duplicate" };
  return map[st.value] || st.value || "Unknown";
});
</script>
