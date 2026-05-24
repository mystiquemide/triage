<template>
  <span :title="address" class="font-mono text-xs">{{ shortAddress }}</span>
</template>

<script setup>
import { computed } from "vue";
const props = defineProps({ address: String });
const shortAddress = computed(() => {
  if (!props.address) return "";
  const addr = props.address.startsWith("0x") ? props.address : "0x" + props.address;
  return addr.slice(0, 8) + "..." + addr.slice(-6);
});
</script>
