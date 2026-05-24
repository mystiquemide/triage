<template>
  <Suspense>
    <template #default>
      <Transition name="fade" mode="out-in">
        <LandingPage v-if="showLanding" @enter="enterApp" />
        <SecurityBountyScreen v-else @exit="exitApp" />
      </Transition>
    </template>
    <template #fallback>
      <div class="flex items-center justify-center h-screen bg-gray-900 text-gray-100">
        <div class="animate-pulse text-xl">Loading SecurityBounty...</div>
      </div>
    </template>
  </Suspense>
</template>

<script setup>
import { ref } from "vue";
import LandingPage from "./components/LandingPage.vue";
import SecurityBountyScreen from "./components/SecurityBountyScreen.vue";

const showLanding = ref(true);

const enterApp = () => {
  sessionStorage.setItem("sb_connect_on_enter", "true");
  showLanding.value = false;
};

const exitApp = () => {
  showLanding.value = true;
};
</script>
