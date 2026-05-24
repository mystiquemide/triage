<template>
  <span
    :class="{
      'text-red-400 bg-red-900 bg-opacity-30': sev === 'critical',
      'text-orange-400 bg-orange-900 bg-opacity-30': sev === 'high',
      'text-yellow-400 bg-yellow-900 bg-opacity-30': sev === 'medium',
      'text-green-400 bg-green-900 bg-opacity-30': sev === 'low',
      'text-gray-400 bg-gray-700': !sev || sev === 'none',
    }"
    class="px-2 py-0.5 rounded text-xs font-medium"
  >
    {{ label }}
  </span>
</template>

<script setup>
import { computed } from "vue";
const props = defineProps({ severity: String });
const sev = computed(() => (props.severity || "none").toLowerCase());
const label = computed(() => {
  const map = { critical: "Critical", high: "High", medium: "Medium", low: "Low", none: "None" };
  return map[sev.value] || sev.value;
});
</script>
