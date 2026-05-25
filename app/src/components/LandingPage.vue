<template>
  <div class="landing-shell" :data-theme="theme">
    <!-- Fading background table -->
    <div class="background-table-container">
      <div class="mock-table">
        <div class="mock-row header"><span>Target</span><span>Severity</span><span>Status</span><span>Reward</span></div>
        <div class="mock-row"><span>0xA1b2...9Fc</span><span class="crit">Critical</span><span>Evaluated</span><span>$5,000</span></div>
        <div class="mock-row"><span>0x4Bc8...1Da</span><span class="high">High</span><span>Evaluated</span><span>$2,500</span></div>
        <div class="mock-row"><span>0x9Fc3...2Eb</span><span class="med">Medium</span><span>Pending</span><span>Pending</span></div>
        <div class="mock-row"><span>0x2Da1...4Fc</span><span class="low">Low</span><span>Evaluated</span><span>$500</span></div>
        <div class="mock-row"><span>0xE8a4...7Bc</span><span class="crit">Critical</span><span>Evaluated</span><span>$10,000</span></div>
        <div class="mock-row"><span>0x1Fc9...8Da</span><span class="high">High</span><span>Pending</span><span>Pending</span></div>
        <div class="mock-row"><span>0xA1b2...9Fc</span><span class="crit">Critical</span><span>Evaluated</span><span>$5,000</span></div>
        <div class="mock-row"><span>0x4Bc8...1Da</span><span class="high">High</span><span>Evaluated</span><span>$2,500</span></div>
        <div class="mock-row"><span>0x9Fc3...2Eb</span><span class="med">Medium</span><span>Pending</span><span>Pending</span></div>
        <div class="mock-row"><span>0x2Da1...4Fc</span><span class="low">Low</span><span>Evaluated</span><span>$500</span></div>
      </div>
    </div>

    <section class="landing-hero borderless-hero">
      <nav class="landing-nav sleek-nav flex justify-between items-center w-full">
        <!-- Left: Logo -->
        <div class="w-1/3 flex justify-start items-center">
          <div class="brand logo-mark-sleek" aria-label="Triage">
            <img class="triage-brand-mark" src="/triage-logo.svg" alt="" aria-hidden="true" />
            <span class="text-logo">Triage</span>
          </div>
        </div>
        <!-- Center: Nav Tabs -->
        <div class="nav-links w-1/3 hidden md:flex justify-center items-center gap-8">
          <a href="#programs">Programs</a>
          <a href="#submit">Submit</a>
          <a href="#reports">Reports</a>
        </div>
        <!-- Right: Actions -->
        <div class="nav-actions w-1/3 flex justify-end items-center gap-4">
          <button class="pill-button primary-pill whitespace-nowrap" @click="enterApp">Connect Wallet</button>
        </div>
      </nav>

      <div id="home" class="hero-copy glass-hero">
        <h1>The smartest <span class="text-accent-mono">bug bounty</span><br/>filter</h1>

        <div class="glass-card">
          <div class="card-header">
            <h3>Search bug programs</h3>
          </div>
          <div class="card-body space-y-4">
            <div class="relative">
              <input type="text" class="sleek-input !pl-10 !bg-white/5 border-white/10 text-sm placeholder-gray-500" placeholder="Search protocol, contract, or ID..." readonly />
              <svg class="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <div class="flex gap-2">
              <button class="pill-button action-pill active !text-[10px] !py-1.5 !px-3">
                Active bounties
              </button>
              <button class="pill-button action-pill !text-[10px] !py-1.5 !px-3">
                Smart Contracts
              </button>
              <button class="pill-button action-pill !text-[10px] !py-1.5 !px-3">
                High Rewards
              </button>
            </div>
          </div>
          <div class="card-footer">
            <button class="pill-button submit-pill" @click="enterApp">Start screening</button>
          </div>
        </div>
      </div>
    </section>

    <!-- FOOTER -->
    <footer class="border-t border-white border-opacity-10 py-8 relative z-10 bg-black bg-opacity-40 backdrop-blur-sm mt-20">
      <div class="max-w-[1400px] mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-4">
        <p class="text-[10px] text-gray-500 uppercase tracking-widest font-mono">
          &copy; 2026 Triage. All rights reserved.
        </p>
        <div class="flex items-center gap-6 text-gray-400">
          <span class="text-[10px] text-gray-500 uppercase tracking-widest font-mono flex items-center gap-2">
            Powered by GenLayer
          </span>
          <a href="#" class="hover:text-white transition-colors" aria-label="X (Twitter)">
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 7.584H.474l8.6-9.83L0 1.154h7.594l5.243 6.932ZM17.61 20.644h2.039L6.486 3.24H4.298Z"/></svg>
          </a>
          <a href="#" class="hover:text-white transition-colors" aria-label="Documentation">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
          </a>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { connectEvmWallet } from "../services/genlayer";
import { ref } from "vue";

const emit = defineEmits(["enter"]);
const theme = ref("dark");

const enterApp = async () => {
  try {
    const address = await connectEvmWallet();
    if (address) {
      emit("enter");
    }
  } catch (error) {
    console.error(error);
  }
};

const workflow = [
  { step: "01", title: "Define Scope", text: "Publish targets, exclusions, rules, and safe harbor in one brief." },
  { step: "02", title: "Receive Reports", text: "Researchers submit title, impact, reproduction steps, proof, and links." },
  { step: "03", title: "Evaluate Risk", text: "Triage submissions by severity, reproducibility, and program fit." },
  { step: "04", title: "Track Outcomes", text: "Accepted findings feed the vulnerability registry and reward flow." },
];

</script>
