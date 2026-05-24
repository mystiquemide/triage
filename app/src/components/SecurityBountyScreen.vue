<template>
  <div class="app-shell min-h-screen flex flex-col">
    <!-- Updated Header -->
    <header class="py-4 border-b border-white border-opacity-10 relative">
      <div class="max-w-[1400px] mx-auto px-6 flex justify-between items-center h-10 gap-4">
        <!-- Left: Logo -->
        <div class="flex-1 flex justify-start items-center">
          <div class="brand logo-mark-sleek" aria-label="Triage">
            <span class="text-logo">Triage</span>
          </div>
        </div>

        <!-- Center: Nav Tabs (Desktop) -->
        <div class="hidden lg:flex justify-center items-center gap-2 shrink-0">
          <button v-for="t in tabs" :key="t.id" @click="tab=t.id" class="tab-pill whitespace-nowrap" :class="{'active': tab===t.id}">{{ t.label }}</button>
        </div>

        <!-- Right: Wallet / Disconnect -->
        <div class="flex-1 flex justify-end items-center gap-4">
          <div v-if="evmAddress" class="wallet-cluster">
            <button @click="loadWalletBalance" class="wallet-balance-chip" title="Refresh wallet balance">
              <span class="wallet-chip-label">Balance</span>
              <span class="wallet-chip-value">{{ walletBalanceLabel }}</span>
            </button>
            <div class="wallet-address-chip" :title="evmAddress">
              <span class="hidden xl:inline">{{ evmAddress.slice(0,8) }}...{{ evmAddress.slice(-6) }}</span>
              <span class="hidden lg:inline xl:hidden">{{ evmAddress.slice(0,6) }}...</span>
              <span class="lg:hidden">{{ evmAddress.slice(0,6) }}...</span>
            </div>
            <a
              :href="GENLAYER_FAUCET_URL"
              target="_blank"
              rel="noreferrer"
              class="wallet-faucet-link"
              title="Open GenLayer testnet faucet"
            >
              Faucet
            </a>
            <button @click="disconnect" class="pill-button secondary-pill !text-xs !py-1 !px-2 md:!py-2 md:!px-4">Disconnect</button>
          </div>
        </div>
      </div>

      <!-- Center: Nav Tabs (Mobile) -->
      <div class="lg:hidden flex justify-start md:justify-center gap-2 overflow-x-auto hide-scrollbar px-6 pb-2 mt-4">
         <button v-for="t in tabs" :key="t.id" @click="tab=t.id" class="tab-pill whitespace-nowrap" :class="{'active': tab===t.id}">{{ t.label }}</button>
      </div>
    </header>

    <main class="flex-1 w-full max-w-[1400px] mx-auto px-6 py-12">
      <Transition name="slide-fade" mode="out-in">
        <!-- PROGRAMS -->
        <div v-if="tab==='programs'" key="programs">
          <div class="flex justify-between items-center mb-8">
            <h2 class="text-3xl font-bold">Active Programs</h2>
            <button v-if="evmAddress" @click="showCreate=true" class="pill-button primary-pill">Create Program</button>
          </div>
          <div v-if="isLoading" class="grid lg:grid-cols-2 gap-6 mt-8">
            <div v-for="i in 4" :key="i" class="internal-card animate-pulse border-white border-opacity-5 border-dashed min-h-[250px] flex flex-col justify-between">
               <div>
                 <div class="h-6 bg-white bg-opacity-5 rounded w-1/2 mb-2"></div>
                 <div class="h-4 bg-white bg-opacity-5 rounded w-1/3 mb-8"></div>
                 <div class="h-16 bg-white bg-opacity-5 rounded w-full mb-6"></div>
               </div>
               <div class="flex gap-3"><div class="h-10 bg-white bg-opacity-5 rounded w-full"></div><div class="h-10 bg-white bg-opacity-5 rounded w-full"></div></div>
            </div>
          </div>
          <div v-else-if="!programs.length" class="internal-card text-center py-24 flex flex-col items-center justify-center border-dashed border-opacity-20 mt-8">
            <svg class="w-12 h-12 text-gray-600 mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>
            <h3 class="text-lg font-bold text-gray-300 mb-1">No Active Programs</h3>
            <p class="text-sm text-gray-500 mono-text">Check back later or deploy a new program.</p>
          </div>
          <div v-else class="grid lg:grid-cols-2 gap-6">
            <div v-for="p in programs" :key="p.id" class="internal-card flex flex-col justify-between">
              <div>
                <div class="flex justify-between items-start mb-4">
                  <div>
                    <h3 class="text-xl font-semibold mb-1">{{ p.protocol_name }}</h3>
                    <p class="text-xs text-gray-400 mono-text">Target: {{ shortTarget(p.contract_address) }}</p>
                  </div>
                  <div class="text-right">
                    <span :class="p.is_active?'text-emerald-400':'text-red-400'" class="text-[10px] font-bold px-2 py-1 bg-black bg-opacity-40 rounded uppercase tracking-wider border border-white border-opacity-5">{{ p.is_active?'Active':'Inactive' }}</span>
                  </div>
                </div>
                <p v-if="programMeta(p).brief || p.description" class="text-sm text-gray-400 leading-relaxed">{{ programMeta(p).brief || p.description }}</p>

                <div class="mt-6 mb-6 p-4 bg-black bg-opacity-30 rounded-lg grid grid-cols-2 gap-4 border border-white border-opacity-5">
                  <div><span class="block text-[10px] text-gray-500 uppercase tracking-wider mb-1">Max Bounty</span><span class="font-bold text-emerald-400">{{ formatAmt(p.max_payout) }} GEN</span></div>
                  <div><span class="block text-[10px] text-gray-500 uppercase tracking-wider mb-1">Total Pool</span><span class="font-bold text-gray-200">{{ formatAmt(p.reward_pool) }} GEN</span></div>
                  <div><span class="block text-[10px] text-gray-500 uppercase tracking-wider mb-1">Escrow</span><span class="font-bold" :class="isProgramFunded(p) ? 'text-emerald-400' : 'text-yellow-400'">{{ formatAmt(p.escrow_balance) }} GEN</span></div>
                  <div><span class="block text-[10px] text-gray-500 uppercase tracking-wider mb-1">Funding</span><span class="font-bold" :class="isProgramFunded(p) ? 'text-emerald-400' : 'text-yellow-400'">{{ isProgramFunded(p) ? 'Ready' : 'Unfunded' }}</span></div>
                </div>
              </div>

              <div v-if="evmAddress && isProgramActive(p)" class="mb-3 grid grid-cols-[1fr_auto] gap-2">
                <input v-model="fundDrafts[p.id]" type="number" min="0" class="sleek-input mono-text text-sm" placeholder="Escrow amount" />
                <button @click="fundProgram(p)" :disabled="funding===p.id" class="pill-button secondary-pill !px-4">{{ funding===p.id ? 'Funding...' : 'Fund' }}</button>
              </div>
              <div class="flex gap-3">
                <button @click="selectProgram(p)" class="pill-button action-pill w-full justify-center">View Brief</button>
                <button v-if="evmAddress && isProgramActive(p)" @click="startReport(p)" class="pill-button action-pill active w-full justify-center text-emerald-300">Submit Bug</button>
              </div>
            </div>
          </div>
          <div v-if="selectedProgram" class="internal-card mt-8">
            <div class="flex justify-between items-start mb-6 border-b border-white border-opacity-10 pb-4">
              <div>
                <h3 class="text-2xl text-emerald-400 font-bold mb-1">{{ selectedProgram.protocol_name }} <span class="text-gray-200">Brief</span></h3>
                <p class="text-sm text-gray-500 mono-text">{{ selectedProgram.contract_address }}</p>
              </div>
              <button @click="selectedProgram=null" class="pill-button secondary-pill">Close Brief</button>
            </div>
            <div class="grid md:grid-cols-2 gap-8 text-sm">
              <section><h4 class="text-gray-500 text-[10px] font-bold uppercase tracking-widest mb-2">Overview</h4><p class="text-gray-300 whitespace-pre-wrap leading-relaxed">{{ programMeta(selectedProgram).brief || selectedProgram.description || "No brief provided." }}</p></section>
              <section><h4 class="text-gray-500 text-[10px] font-bold uppercase tracking-widest mb-2">Rewards</h4><p class="text-gray-300 whitespace-pre-wrap leading-relaxed">{{ programMeta(selectedProgram).rewardTable || `Max payout: ${formatAmt(selectedProgram.max_payout)} GEN` }}</p></section>
              <section><h4 class="text-gray-500 text-[10px] font-bold uppercase tracking-widest mb-2">In Scope</h4><p class="text-gray-300 whitespace-pre-wrap leading-relaxed">{{ programMeta(selectedProgram).inScope || selectedProgram.contract_address || "No scope provided." }}</p></section>
              <section><h4 class="text-gray-500 text-[10px] font-bold uppercase tracking-widest mb-2">Out Of Scope</h4><p class="text-gray-300 whitespace-pre-wrap leading-relaxed">{{ programMeta(selectedProgram).outOfScope || "No exclusions listed." }}</p></section>
              <section><h4 class="text-gray-500 text-[10px] font-bold uppercase tracking-widest mb-2">Rules</h4><p class="text-gray-300 whitespace-pre-wrap leading-relaxed">{{ programMeta(selectedProgram).rules || "No rules listed." }}</p></section>
              <section><h4 class="text-gray-500 text-[10px] font-bold uppercase tracking-widest mb-2">Safe Harbor</h4><p class="text-gray-300 whitespace-pre-wrap leading-relaxed">{{ programMeta(selectedProgram).safeHarbor || "No safe harbor statement provided." }}</p></section>
              <section><h4 class="text-gray-500 text-[10px] font-bold uppercase tracking-widest mb-2">Disclosure</h4><p class="text-gray-300 whitespace-pre-wrap leading-relaxed">{{ programMeta(selectedProgram).disclosurePolicy || "No disclosure policy provided." }}</p></section>
              <section><h4 class="text-gray-500 text-[10px] font-bold uppercase tracking-widest mb-2">Total Pool</h4><p class="text-emerald-400 font-bold whitespace-pre-wrap leading-relaxed">{{ formatAmt(selectedProgram.reward_pool) }} GEN</p></section>
              <section><h4 class="text-gray-500 text-[10px] font-bold uppercase tracking-widest mb-2">Escrow</h4><p class="font-bold whitespace-pre-wrap leading-relaxed" :class="isProgramFunded(selectedProgram) ? 'text-emerald-400' : 'text-yellow-400'">{{ formatAmt(selectedProgram.escrow_balance) }} GEN {{ isProgramFunded(selectedProgram) ? 'available' : 'needed before payout' }}</p></section>
            </div>
          </div>
        </div>

        <!-- SUBMIT -->
        <div v-else-if="tab==='submit'" key="submit">
          <div v-if="!evmAddress" class="internal-card text-center py-24 flex flex-col items-center justify-center border-dashed border-opacity-20 mt-8">
            <svg class="w-12 h-12 text-gray-600 mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
            <h3 class="text-lg font-bold text-gray-300 mb-1">Wallet Disconnected</h3>
            <p class="text-sm text-gray-500 mono-text">Please connect your wallet to submit a bug report.</p>
          </div>
          <div v-else class="internal-card max-w-3xl mx-auto">
            <h2 class="text-2xl font-bold mb-6">Submit Bug Report</h2>
            <div class="space-y-5">
              <div>
                <label class="block text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-2">Program <span class="text-red-400">*</span></label>
                <div class="flex gap-2">
                <select v-model="rf.programId" :class="fieldClass('programId')" data-report-field="programId">
                  <option value="" disabled>Select program</option>
                  <option v-for="p in selectablePrograms" :key="p.id" :value="p.id">{{ p.protocol_name }}{{ isProgramActive(p) ? "" : " (inactive)" }}</option>
                </select>
                <button @click="loadPrograms" class="pill-button secondary-pill !py-2 !px-4">Refresh</button>
                </div>
              </div>
              <p v-if="evmAddress && !selectablePrograms.length" class="text-xs text-yellow-400">No programs loaded yet. Refresh once the create transaction finalizes.</p>
              <div>
                <label class="block text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-2">Affected target</label>
                <input v-model="rf.affectedTarget" class="sleek-input" placeholder="Contract, URL, repo path, function" />
              </div>
              <div class="grid md:grid-cols-2 gap-5">
                <div>
                  <label class="block text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-2">Category</label>
                  <input v-model="rf.category" class="sleek-input" placeholder="Reentrancy, access control..." />
                </div>
                <div>
                  <label class="block text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-2">Severity</label>
                  <select v-model="rf.severity" class="sleek-input"><option value="" disabled>Severity</option><option value="critical">Critical</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select>
                </div>
              </div>
              <div>
                <label class="block text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-2">Title <span class="text-red-400">*</span></label>
                <input v-model="rf.title" :class="fieldClass('title')" data-report-field="title" placeholder="Short vulnerability title" />
              </div>
              <div>
                <label class="block text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-2">Technical description</label>
                <textarea v-model="rf.desc" rows="3" class="sleek-input mono-text text-sm" placeholder="Explain the bug and affected behavior"></textarea>
              </div>
              <div>
                <label class="block text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-2">Impact <span class="text-red-400">*</span></label>
                <textarea v-model="rf.impact" rows="2" :class="fieldClass('impact')" data-report-field="impact" placeholder="What can an attacker do?"></textarea>
              </div>
              <div>
                <label class="block text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-2">Reproduction steps <span class="text-red-400">*</span></label>
                <textarea v-model="rf.steps" rows="3" :class="fieldClass('steps')" data-report-field="steps" placeholder="Step-by-step instructions to reproduce"></textarea>
              </div>
              <div>
                <label class="block text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-2">Proof of concept</label>
                <textarea v-model="rf.proof" rows="2" class="sleek-input mono-text text-sm" placeholder="PoC code or transaction details"></textarea>
              </div>
              <div class="grid md:grid-cols-2 gap-5">
                <div>
                  <label class="block text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-2">Code links</label>
                  <textarea v-model="rf.links" rows="2" class="sleek-input" placeholder="One link per line"></textarea>
                </div>
                <div>
                  <label class="block text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-2">Suggested remediation</label>
                  <textarea v-model="rf.remediation" rows="2" class="sleek-input" placeholder="Optional fix guidance"></textarea>
                </div>
              </div>
              <div class="pt-4 flex flex-col items-end">
                <p v-if="submitTried && missingReportFields.length" class="text-xs text-red-400 mb-3 font-bold">Missing: {{ missingReportFields.join(", ") }}.</p>
                <button @click="submit" :disabled="submitting" class="pill-button primary-pill w-full md:w-auto !px-12">{{ submitting?'Submitting...':'Submit Report' }}</button>
              </div>
            </div>
          </div>
        </div>

        <!-- REPORTS -->
        <div v-else-if="tab==='reports'" key="reports">
          <h2 class="text-3xl font-bold mb-8">Reports Pipeline</h2>
          <div v-if="isLoadingReports" class="space-y-4 mt-8">
            <div v-for="i in 3" :key="i" class="internal-card animate-pulse border-white border-opacity-5 border-dashed h-[60px] flex items-center px-6">
              <div class="h-4 bg-white bg-opacity-5 rounded w-1/4"></div>
              <div class="h-4 bg-white bg-opacity-5 rounded w-1/4 ml-auto"></div>
            </div>
          </div>
          <div v-else-if="!reports.length" class="internal-card text-center py-24 flex flex-col items-center justify-center border-dashed border-opacity-20 mt-8">
            <svg class="w-12 h-12 text-gray-600 mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
            <h3 class="text-lg font-bold text-gray-300 mb-1">No Reports Available</h3>
            <p class="text-sm text-gray-500 mono-text">The pipeline is currently empty.</p>
          </div>
          <div v-else class="internal-card !p-0 overflow-hidden overflow-x-auto">
            <table class="w-full text-left border-collapse">
              <thead class="bg-black bg-opacity-40 border-b border-white border-opacity-10">
                <tr>
                  <th class="px-6 py-4 text-[10px] uppercase tracking-widest text-gray-500 font-bold">Title</th>
                  <th class="px-6 py-4 text-[10px] uppercase tracking-widest text-gray-500 font-bold">Category</th>
                  <th class="px-6 py-4 text-[10px] uppercase tracking-widest text-gray-500 font-bold">Submitter</th>
                  <th class="px-6 py-4 text-[10px] uppercase tracking-widest text-gray-500 font-bold">Status</th>
                  <th class="px-6 py-4 text-[10px] uppercase tracking-widest text-gray-500 font-bold">Reward</th>
                  <th class="px-6 py-4 text-[10px] uppercase tracking-widest text-gray-500 font-bold">Payout</th>
                  <th class="px-6 py-4 text-[10px] uppercase tracking-widest text-gray-500 font-bold text-right">Action</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-white divide-opacity-5">
                <tr v-for="r in reports" :key="r.id" class="hover:bg-white hover:bg-opacity-5 transition-colors">
                  <td class="px-6 py-4 text-sm font-medium">{{ r.title }}</td>
                  <td class="px-6 py-4 text-xs text-gray-400 mono-text">{{ reportMeta(r).category || "-" }}</td>
                  <td class="px-6 py-4 text-xs font-mono text-gray-500">{{ r.submitter?.slice(0,10) }}...</td>
                  <td class="px-6 py-4"><span :class="statusClass(r.status)" class="text-[10px] font-bold uppercase tracking-widest px-2 py-1 bg-black bg-opacity-50 rounded border border-white border-opacity-5">{{ r.status }}</span></td>
                  <td class="px-6 py-4 text-xs font-bold text-emerald-400 mono-text">{{ formatAmt(r.reward) }}</td>
                  <td class="px-6 py-4"><span :class="payoutClass(r.payout_status)" class="text-[10px] font-bold uppercase tracking-widest px-2 py-1 bg-black bg-opacity-50 rounded border border-white border-opacity-5">{{ payoutLabel(r) }}</span></td>
                  <td class="px-6 py-4 text-right">
                    <div class="flex justify-end gap-2">
                      <button @click="selectedReport=r" class="pill-button action-pill !text-xs">View</button>
                      <button v-if="r.status==='pending'" @click="evaluate(r.id)" :disabled="evaluating===r.id || !isReportProgramFunded(r)" class="pill-button secondary-pill !text-xs">{{ evaluating===r.id?'Evaluating...':isReportProgramFunded(r)?'Evaluate':'Fund First' }}</button>
                      <button v-if="canRetryPayout(r)" @click="retryPayout(r.id)" :disabled="retryingPayout===r.id" class="pill-button secondary-pill !text-xs">{{ retryingPayout===r.id?'Retrying...':'Retry Payout' }}</button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>



        <!-- LEADERBOARD -->
        <div v-else-if="tab==='leaderboard'" key="leaderboard">
          <h2 class="text-3xl font-bold mb-8">Leaderboard</h2>
          <div v-if="!leaderboard.length" class="internal-card text-center py-24 flex flex-col items-center justify-center border-dashed border-opacity-20 mt-8">
            <svg class="w-12 h-12 text-gray-600 mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
            <h3 class="text-lg font-bold text-gray-300 mb-1">No Hackers Yet</h3>
            <p class="text-sm text-gray-500 mono-text">The leaderboard will populate once bounties are paid.</p>
          </div>
          <div v-else class="space-y-3">
            <div v-for="(hacker, idx) in leaderboard" :key="hacker.address" class="internal-card flex justify-between items-center hover:border-white hover:border-opacity-20 transition-all">
              <div class="flex items-center gap-6">
                <div class="text-2xl font-bold font-mono min-w-[30px]" :class="idx===0?'text-yellow-400':idx===1?'text-gray-300':idx===2?'text-orange-400':'text-gray-600'">
                  #{{ idx + 1 }}
                </div>
                <div>
                  <p class="font-semibold mb-1 mono-text">{{ hacker.address }}</p>
                  <span class="text-[10px] text-gray-500 uppercase tracking-widest mono-text">{{ hacker.bugCount }} valid finding{{ hacker.bugCount !== 1 ? 's' : '' }}</span>
                </div>
              </div>
              <div class="text-right">
                <span class="text-xl font-bold text-emerald-400 mono-text">{{ formatAmt(hacker.totalReward) }} GEN</span>
              </div>
            </div>
          </div>
        </div>

        <!-- MY REPORTS -->
        <div v-else-if="tab==='myreports'" key="myreports">
          <h2 class="text-3xl font-bold mb-8">My Reports</h2>
          <div v-if="!evmAddress" class="internal-card text-center py-24 flex flex-col items-center justify-center border-dashed border-opacity-20 mt-8">
            <svg class="w-12 h-12 text-gray-600 mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
            <h3 class="text-lg font-bold text-gray-300 mb-1">Wallet Required</h3>
            <p class="text-sm text-gray-500 mono-text">Connect your wallet to view your submitted reports.</p>
          </div>
          <div v-else-if="isLoadingReports" class="space-y-4 mt-8">
            <div v-for="i in 3" :key="i" class="internal-card animate-pulse border-white border-opacity-5 border-dashed h-[60px] flex items-center px-6">
              <div class="h-4 bg-white bg-opacity-5 rounded w-1/4"></div>
              <div class="h-4 bg-white bg-opacity-5 rounded w-1/4 ml-auto"></div>
            </div>
          </div>
          <div v-else-if="!myReports.length" class="internal-card text-center py-24 flex flex-col items-center justify-center border-dashed border-opacity-20 mt-8">
            <svg class="w-12 h-12 text-gray-600 mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 19v-8.93a2 2 0 01.89-1.664l7-4.666a2 2 0 012.22 0l7 4.666A2 2 0 0121 10.07V19M3 19a2 2 0 002 2h14a2 2 0 002-2M3 19l6.75-4.5M21 19l-6.75-4.5M3 10l6.75 4.5M21 10l-6.75 4.5m0 0l-1.14.76a2 2 0 01-2.22 0l-1.14-.76" /></svg>
            <h3 class="text-lg font-bold text-gray-300 mb-1">No Submissions Yet</h3>
            <p class="text-sm text-gray-500 mono-text">You haven't submitted any reports to the active programs.</p>
          </div>
          <div v-else class="space-y-3">
            <div v-for="r in myReports" :key="r.id" @click="selectedReport=r" class="internal-card flex justify-between items-center hover:border-white hover:border-opacity-20 transition-all cursor-pointer">
              <div>
                <p class="font-semibold mb-1">{{ r.title }}</p>
                <span class="text-[10px] text-gray-500 uppercase tracking-widest mono-text">ID: {{ r.id }}</span>
              </div>
              <div class="text-right flex flex-col items-end gap-2">
                <div class="flex items-center gap-2">
                  <span v-if="r.reward&&r.reward!=='0'" class="text-xs font-bold text-emerald-400 mono-text">+{{ formatAmt(r.reward) }} GEN</span>
                  <span :class="{pending:'text-yellow-400',accepted:'text-emerald-400',rejected:'text-red-400'}[r.status]||'text-gray-400'" class="text-[10px] font-bold uppercase tracking-widest px-2 py-1 bg-black bg-opacity-50 rounded border border-white border-opacity-5">{{ r.status }}</span>
                </div>
                <button @click.stop="selectedReport=r" class="pill-button action-pill !text-xs mt-1">View Details</button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </main>

    <!-- CREATE PROGRAM MODAL -->
    <div v-if="showCreate" class="fixed inset-0 bg-black bg-opacity-80 backdrop-blur-md flex items-center justify-center z-50 p-4">
      <div class="internal-card w-full max-w-4xl max-h-[90vh] overflow-y-auto relative">
        <button @click="showCreate=false" class="absolute top-6 right-6 text-gray-500 hover:text-white transition-colors">✕</button>
        <h3 class="text-2xl font-bold mb-6">New Program</h3>

        <div class="space-y-4">
          <div class="grid md:grid-cols-2 gap-4">
            <div><label class="block text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Protocol Name</label><input v-model="cf.name" class="sleek-input" placeholder="e.g. JudgeNet Core" /></div>
            <div><label class="block text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Target Contract</label><input v-model="cf.target" class="sleek-input mono-text text-sm" placeholder="0x..." /></div>
          </div>
          <div><label class="block text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Short Description</label><textarea v-model="cf.desc" rows="2" class="sleek-input" placeholder="One sentence summary of the bounty"></textarea></div>
          <div><label class="block text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Program Brief</label><textarea v-model="cf.brief" rows="3" class="sleek-input" placeholder="Detailed overview of the program goals"></textarea></div>

          <div class="grid md:grid-cols-2 gap-4">
            <div><label class="block text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">In Scope</label><textarea v-model="cf.inScope" rows="3" class="sleek-input mono-text text-sm" placeholder="Contracts and assets in scope"></textarea></div>
            <div><label class="block text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Out of Scope</label><textarea v-model="cf.outOfScope" rows="3" class="sleek-input mono-text text-sm" placeholder="Excluded targets"></textarea></div>
          </div>

          <div class="grid md:grid-cols-2 gap-4">
            <div><label class="block text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Rules</label><textarea v-model="cf.rules" rows="2" class="sleek-input" placeholder="Prohibited testing methods (e.g. DoS)"></textarea></div>
            <div><label class="block text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Safe Harbor</label><textarea v-model="cf.safeHarbor" rows="2" class="sleek-input" placeholder="Legal protections for hackers"></textarea></div>
          </div>

          <div class="grid md:grid-cols-2 gap-4">
            <div><label class="block text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Disclosure Policy</label><textarea v-model="cf.disclosurePolicy" rows="2" class="sleek-input" placeholder="Rules for publishing bugs"></textarea></div>
            <div><label class="block text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Reward Table</label><textarea v-model="cf.rewardTable" rows="2" class="sleek-input mono-text text-sm" placeholder="Critical: 50k, High: 10k..."></textarea></div>
          </div>

          <div class="grid md:grid-cols-3 gap-4 p-4 bg-black bg-opacity-30 border border-white border-opacity-5 rounded-lg">
            <div><label class="block text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Total Pool (GEN)</label><input v-model.number="cf.pool" type="number" class="sleek-input font-bold text-emerald-400" placeholder="1000000" /></div>
            <div><label class="block text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Max Payout (GEN)</label><input v-model.number="cf.max" type="number" class="sleek-input font-bold text-emerald-400" placeholder="50000" /></div>
            <div><label class="block text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Fund Now (GEN)</label><input v-model.number="cf.escrow" type="number" min="0" class="sleek-input font-bold text-emerald-400" placeholder="0" /></div>
          </div>

          <div class="flex justify-end gap-3 pt-4 border-t border-white border-opacity-10">
            <button @click="showCreate=false" class="pill-button secondary-pill">Cancel</button>
            <button @click="createProgram" :disabled="creating" class="pill-button primary-pill px-8">{{ creating?'Deploying Program...':'Launch Program' }}</button>
          </div>
        </div>
      </div>
    </div>

    <!-- REPORT DETAILS MODAL -->
    <div v-if="selectedReport" class="fixed inset-0 bg-black bg-opacity-80 backdrop-blur-md flex items-center justify-center z-50 p-4">
      <div class="internal-card w-full max-w-4xl max-h-[90vh] overflow-y-auto relative">
        <button @click="selectedReport=null" class="absolute top-6 right-6 text-gray-500 hover:text-white transition-colors">✕</button>
        <div class="flex justify-between items-start mb-6 border-b border-white border-opacity-10 pb-4 pr-8">
          <div>
            <h3 class="text-2xl font-bold mb-1">{{ selectedReport.title }}</h3>
            <p class="text-sm text-gray-400 mono-text">Report ID: {{ selectedReport.id }} &bull; Submitted by: {{ selectedReport.submitter }}</p>
          </div>
          <div class="text-right flex flex-col items-end">
             <span :class="statusClass(selectedReport.status)" class="text-[10px] font-bold uppercase tracking-widest px-2 py-1 bg-black bg-opacity-50 rounded border border-white border-opacity-5">{{ selectedReport.status }}</span>
             <div v-if="selectedReport.reward&&selectedReport.reward!=='0'" class="mt-2 text-xs font-bold text-emerald-400 mono-text">+{{ formatAmt(selectedReport.reward) }} GEN</div>
             <div v-if="selectedReport.payout_status" class="mt-2 flex flex-col items-end gap-2">
               <span :class="payoutClass(selectedReport.payout_status)" class="text-[10px] font-bold uppercase tracking-widest px-2 py-1 bg-black bg-opacity-50 rounded border border-white border-opacity-5">{{ payoutLabel(selectedReport) }}</span>
               <button v-if="canRetryPayout(selectedReport)" @click="retryPayout(selectedReport.id)" :disabled="retryingPayout===selectedReport.id" class="pill-button secondary-pill !text-xs">{{ retryingPayout===selectedReport.id?'Retrying...':'Retry Payout' }}</button>
             </div>
          </div>
        </div>

        <div class="space-y-8 text-sm">
          <section>
            <h4 class="text-gray-500 text-[10px] font-bold uppercase tracking-widest mb-3">Technical Description</h4>
            <div class="prose prose-invert max-w-none text-gray-300 markdown-content" v-html="parsedReportDesc"></div>
          </section>
          <section v-if="reportMeta(selectedReport).impact">
            <h4 class="text-gray-500 text-[10px] font-bold uppercase tracking-widest mb-3">Impact</h4>
            <div class="prose prose-invert max-w-none text-gray-300 markdown-content" v-html="parsedReportImpact"></div>
          </section>
          <section v-if="reportMeta(selectedReport).steps">
            <h4 class="text-gray-500 text-[10px] font-bold uppercase tracking-widest mb-3">Reproduction Steps</h4>
            <div class="prose prose-invert max-w-none text-gray-300 markdown-content" v-html="parsedReportSteps"></div>
          </section>
          <section v-if="reportMeta(selectedReport).proof">
            <h4 class="text-gray-500 text-[10px] font-bold uppercase tracking-widest mb-3">Proof of Concept</h4>
            <div class="prose prose-invert max-w-none text-gray-300 markdown-content" v-html="parsedReportProof"></div>
          </section>
          <section v-if="reportMeta(selectedReport).remediation">
            <h4 class="text-gray-500 text-[10px] font-bold uppercase tracking-widest mb-3">Suggested Remediation</h4>
            <div class="prose prose-invert max-w-none text-gray-300 markdown-content" v-html="parsedReportRemediation"></div>
          </section>
        </div>
        <div class="mt-8 pt-4 border-t border-white border-opacity-10 flex justify-end">
           <button @click="selectedReport=null" class="pill-button secondary-pill">Close</button>
        </div>
      </div>
    </div>

    <!-- Toast -->
    <Transition name="toast-slide">
      <div v-if="toast" class="fixed bottom-6 right-6 z-50 max-w-sm w-full shadow-2xl">
        <div class="internal-card !p-4 flex items-center gap-3 backdrop-blur-xl bg-black bg-opacity-80 border" :class="toast.t==='err'?'border-red-500/30':'border-emerald-500/30'">
          <div class="flex-shrink-0">
            <svg v-if="toast.t==='err'" class="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
            <svg v-else class="w-6 h-6 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          </div>
          <div>
            <p class="text-sm font-semibold text-white">{{ toast.t === 'err' ? 'Error' : 'Success' }}</p>
            <p class="text-xs mt-0.5 text-gray-300 leading-tight">{{ toast.m }}</p>
          </div>
        </div>
      </div>
    </Transition>
    <!-- FOOTER -->
    <footer class="border-t border-white border-opacity-10 py-8 mt-auto relative z-10 bg-black bg-opacity-40 backdrop-blur-sm">
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
import { computed, ref, nextTick, onMounted, onBeforeUnmount } from "vue";
import DOMPurify from "dompurify";
import { marked } from "marked";
import {
  getAccount,
  createAccount,
  clearAccount,
  createBountyClient,
  connectEvmWallet,
  getConnectedEvmAddress,
  setConnectedEvmAddress,
} from "../services/genlayer";
import SecurityBounty from "../logic/SecurityBounty";

const contractAddress = import.meta.env.VITE_CONTRACT_ADDRESS;
const GENLAYER_FAUCET_URL = "https://testnet-faucet.genlayer.foundation/";

const account = ref(getAccount());
const client = ref(createBountyClient(account.value));
const sb = new SecurityBounty(contractAddress, client.value);
const evmAddress = ref(getConnectedEvmAddress());
const userAddress = ref(account.value?.address || null);
const walletBalanceWei = ref(null);
const walletBalanceLoading = ref(false);

const emit = defineEmits(["exit"]);

const tab = ref("programs");
const showCreate = ref(false);
const submitting = ref(false);
const creating = ref(false);
const evaluating = ref("");
const funding = ref("");
const retryingPayout = ref("");
const submitTried = ref(false);
const toast = ref(null);
const programs = ref([]);
const reports = ref([]);
const vulns = ref([]);
const myReports = ref([]);
const fundDrafts = ref({});
const selectedProgram = ref(null);
const selectedReport = ref(null);
const isLoading = ref(true);
const isLoadingReports = ref(true);

const tabs = [
  { id: "programs", label: "Programs" },
  { id: "leaderboard", label: "Leaderboard" },
  { id: "submit", label: "Submit" },
  { id: "reports", label: "Reports" },
  { id: "myreports", label: "My Reports" },
];

const blankReport = () => ({ programId: "", affectedTarget: "", category: "", title: "", desc: "", impact: "", steps: "", proof: "", links: "", remediation: "", severity: "" });
const blankProgram = () => ({ name: "", target: "", desc: "", brief: "", inScope: "", outOfScope: "", rules: "", safeHarbor: "", disclosurePolicy: "", rewardTable: "", pool: "", max: "", escrow: "" });
const rf = ref(blankReport());
const cf = ref(blankProgram());

const toast_ = (m, t) => { toast.value = { m, t }; setTimeout(() => toast.value = null, 4000); };
const errorMessage = e => e?.shortMessage || e?.details || e?.message || String(e);
const formatAmt = v => { if(!v||v==="0")return"0"; const n=typeof v==="string"?parseInt(v):Number(v); return n>=1e6?(n/1e6).toFixed(1)+"M":n>=1e3?(n/1e3).toFixed(1)+"K":String(n); };
const formatWalletGen = wei => {
  if (wei == null) return "— GEN";
  const value = BigInt(wei);
  if (value === 0n) return "0 GEN";
  const base = 10n ** 18n;
  const whole = value / base;
  const frac = value % base;
  if (whole >= 1000000n) return `${whole.toString()} GEN`;
  const decimals = whole > 0n ? 4 : 6;
  const scale = 10n ** BigInt(18 - decimals);
  const fractional = (frac / scale).toString().padStart(decimals, "0").replace(/0+$/, "");
  return `${whole.toString()}${fractional ? `.${fractional}` : ""} GEN`;
};
const walletBalanceLabel = computed(() => walletBalanceLoading.value ? "Loading..." : formatWalletGen(walletBalanceWei.value));
const parseJson = value => { try { return value ? JSON.parse(value) : {}; } catch { return {}; } };
const programMeta = p => parseJson(p?.program_metadata);
const reportMeta = r => parseJson(r?.report_metadata);
const shortTarget = v => v ? `${v.slice(0,18)}${v.length > 18 ? "..." : ""}` : "No target";
const summarize = v => v ? `${String(v).slice(0, 80)}${String(v).length > 80 ? "..." : ""}` : "-";
const isProgramActive = p => p?.is_active === true || p?.is_active === "true";
const isProgramFunded = p => Number.parseInt(String(p?.escrow_balance || "0"), 10) > 0;
const isReportProgramFunded = r => {
  const program = programs.value.find(p => p.id === r?.program_id);
  return isProgramFunded(program);
};
const positiveAmount = value => {
  const amount = BigInt(String(value || "0"));
  if (amount <= 0n) throw new Error("Enter a positive escrow amount.");
  return amount;
};

const parsedReportDesc = computed(() => DOMPurify.sanitize(marked.parse(selectedReport.value?.description || "")));
const parsedReportImpact = computed(() => DOMPurify.sanitize(marked.parse(reportMeta(selectedReport.value)?.impact || "")));
const parsedReportSteps = computed(() => DOMPurify.sanitize(marked.parse(reportMeta(selectedReport.value)?.steps || "")));
const parsedReportProof = computed(() => DOMPurify.sanitize(marked.parse(reportMeta(selectedReport.value)?.proof || "")));
const parsedReportRemediation = computed(() => DOMPurify.sanitize(marked.parse(reportMeta(selectedReport.value)?.remediation || "")));

const leaderboard = computed(() => {
  const stats = {};
  for (const r of reports.value) {
    if (r.status === "accepted" || r.status === "resolved") {
      const reward = typeof r.reward === "string" ? parseInt(r.reward) : Number(r.reward || 0);
      if (reward > 0) {
        if (!stats[r.submitter]) stats[r.submitter] = { address: r.submitter, totalReward: 0, bugCount: 0 };
        stats[r.submitter].totalReward += reward;
        stats[r.submitter].bugCount += 1;
      }
    }
  }
  return Object.values(stats).sort((a, b) => b.totalReward - a.totalReward);
});
const selectablePrograms = computed(() => programs.value);
const requiredReportFields = [
  ["programId", "program"],
  ["title", "title"],
  ["impact", "impact"],
  ["steps", "reproduction steps"],
];
const missingReportFields = computed(() => requiredReportFields.filter(([field]) => !String(rf.value[field] || "").trim()).map(([, label]) => label));
const fieldClass = field => [
  "w-full bg-gray-700 border rounded px-3 py-2 text-sm",
  submitTried.value && !String(rf.value[field] || "").trim() ? "border-red-500 ring-1 ring-red-500" : "border-gray-600",
];
const statusClass = s => ({ pending:"text-yellow-400", accepted:"text-green-400", rejected:"text-red-400", duplicate:"text-orange-400", resolved:"text-emerald-400", needs_info:"text-blue-400", out_of_scope:"text-red-300", not_reproducible:"text-red-300", informational:"text-gray-300" }[s] || "text-gray-400");
const payoutLabel = r => {
  if (!r?.payout_status || r.payout_status === "none") return "-";
  const attempts = Number.parseInt(String(r.payout_attempts || "0"), 10);
  return attempts > 0 ? `${r.payout_status} · ${attempts}/3` : r.payout_status;
};
const payoutClass = s => ({ pending:"text-yellow-400", emitted:"text-emerald-400", none:"text-gray-500" }[s] || "text-gray-400");
const canRetryPayout = r => r?.status === "accepted" && r?.reward && r.reward !== "0" && Number.parseInt(String(r.payout_attempts || "0"), 10) < 3;
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

const loadWalletBalance = async () => {
  const provider = window.ethereum;
  if (!provider?.request || !evmAddress.value) {
    walletBalanceWei.value = null;
    return;
  }
  walletBalanceLoading.value = true;
  try {
    const balance = await provider.request({
      method: "eth_getBalance",
      params: [evmAddress.value, "latest"],
    });
    walletBalanceWei.value = BigInt(balance).toString();
  } catch (e) {
    console.error(e);
    walletBalanceWei.value = null;
  } finally {
    walletBalanceLoading.value = false;
  }
};

const ensureLocalAccount = () => {
  const acc = account.value || createAccount();
  account.value = acc;
  userAddress.value = acc.address;
  const c = createBountyClient(acc);
  client.value = c;
  sb.setClient(c);
  return acc;
};

const connect = async () => {
  try {
    const address = await connectEvmWallet();
    ensureLocalAccount();
    evmAddress.value = address;
    await loadWalletBalance();
    toast_("Wallet connected!", "ok");
    loadMine();
  } catch (e) {
    toast_(e.message || "Wallet connection failed", "err");
  }
};

const disconnect = () => {
  clearAccount();
  account.value = null;
  evmAddress.value = null;
  walletBalanceWei.value = null;
  userAddress.value = null;
  myReports.value = [];
  const c = createBountyClient(null);
  client.value = c;
  sb.setClient(c);
  toast_("Disconnected", "ok");
  emit("exit");
};

const handleAccountsChanged = (accounts) => {
  const address = accounts?.[0] || null;
  setConnectedEvmAddress(address);
  evmAddress.value = address;
  walletBalanceWei.value = null;
  myReports.value = [];
  if (address) {
    ensureLocalAccount();
    loadWalletBalance();
    loadMine();
  }
};

const loadPrograms = async () => {
    isLoading.value = true;
    try {
      const data = await sb.listPrograms();
      programs.value = data;
    } catch (e) {
      toast_(errorMessage(e), "err");
    } finally {
      isLoading.value = false;
    }
  };
  const loadReports = async () => {
    isLoadingReports.value = true;
    try {
      const data = await sb.listReports();
      reports.value = data;
      if (evmAddress.value) {
        myReports.value = data.filter(r => String(r.submitter).toLowerCase() === String(evmAddress.value).toLowerCase());
      }
    } catch (e) {
      toast_(errorMessage(e), "err");
    } finally {
      isLoadingReports.value = false;
    }
  };
const loadVulns    = async () => { try { vulns.value = await sb.getVulnerabilityRegistry(); } catch(e) { console.error(e); } };
const loadMine     = async () => { if(!userAddress.value) return; try { myReports.value = await sb.getHackerReports(userAddress.value); } catch(e) { console.error(e); } };
const refreshProgramsUntil = async (predicate, retries = 10) => {
  for (let i = 0; i < retries; i++) {
    await loadPrograms();
    if (predicate()) return true;
    await sleep(3000);
  }
  return false;
};

const selectProgram = async (program) => {
  try {
    selectedProgram.value = await sb.getProgram(program.id);
  } catch (e) {
    selectedProgram.value = program;
    console.error(e);
  }
};

const startReport = (program) => {
  rf.value.programId = program.id;
  rf.value.affectedTarget = program.contract_address || "";
  tab.value = "submit";
};

const createProgram = async () => {
  if(!cf.value.name||!cf.value.target) return;
  creating.value = true;
  try { ensureLocalAccount(); const name = cf.value.name; const metadata = JSON.stringify({ brief: cf.value.brief, inScope: cf.value.inScope, outOfScope: cf.value.outOfScope, rules: cf.value.rules, safeHarbor: cf.value.safeHarbor, disclosurePolicy: cf.value.disclosurePolicy, rewardTable: cf.value.rewardTable }); const escrowAmount = BigInt(String(cf.value.escrow || "0")); const tx = await sb.createProgram(name, cf.value.target, cf.value.desc||"Bounty", cf.value.pool||1000000, cf.value.max||50000, metadata, escrowAmount); toast_(tx.signer === "browser-wallet" ? "Wallet transaction sent. Waiting for StudioNet..." : "StudioNet wallet transport failed, submitted with GenLayer signer. Waiting...","ok"); showCreate.value=false; cf.value=blankProgram(); await loadWalletBalance(); const expectedId = `${name.toLowerCase().replaceAll(" ", "_")}_61999`; const found = await refreshProgramsUntil(() => programs.value.some(p => p.id === expectedId), 20); const created = programs.value.find(p => p.id === expectedId); if (created) startReport(created); toast_(found ? "Created! Program selected for report submission." : "Transaction sent, but program is not finalized yet. Refresh in a moment.","ok"); }
  catch(e) { toast_(errorMessage(e),"err"); }
  finally { creating.value = false; }
};

const fundProgram = async (program) => {
  if (!program?.id) return;
  funding.value = program.id;
  try {
    ensureLocalAccount();
    const amount = positiveAmount(fundDrafts.value[program.id]);
    const tx = await sb.fundProgram(program.id, amount);
    toast_(tx.signer === "browser-wallet" ? "Funding transaction sent. Waiting for StudioNet..." : "Funding submitted. Waiting for StudioNet...", "ok");
    fundDrafts.value[program.id] = "";
    await loadWalletBalance();
    await refreshProgramsUntil(() => {
      const updated = programs.value.find(p => p.id === program.id);
      return Number.parseInt(String(updated?.escrow_balance || "0"), 10) >= Number.parseInt(String(program.escrow_balance || "0"), 10) + Number(amount);
    }, 20);
    if (selectedProgram.value?.id === program.id) await selectProgram(program);
  } catch (e) {
    toast_(errorMessage(e), "err");
  } finally {
    funding.value = "";
  }
};

const submit = async () => {
  submitTried.value = true;
  const firstMissing = requiredReportFields.find(([field]) => !String(rf.value[field] || "").trim());
  if(firstMissing) {
    toast_(`Add ${missingReportFields.value.join(", ")} before submitting.`, "err");
    await nextTick();
    document.querySelector(`[data-report-field="${firstMissing[0]}"]`)?.scrollIntoView({ behavior: "smooth", block: "center" });
    document.querySelector(`[data-report-field="${firstMissing[0]}"]`)?.focus?.();
    return;
  }
  submitting.value = true;
  try { ensureLocalAccount(); const links=rf.value.links?rf.value.links.split("\n").map(l=>l.trim()).filter(Boolean):[]; const metadata = JSON.stringify({ affectedTarget: rf.value.affectedTarget, category: rf.value.category, impact: rf.value.impact, steps: rf.value.steps, proof: rf.value.proof, remediation: rf.value.remediation }); const tx = await sb.submitReport(rf.value.programId,rf.value.title,rf.value.desc,links,rf.value.severity,metadata); toast_(tx.signer === "browser-wallet" ? "Wallet transaction sent. Waiting for StudioNet..." : "StudioNet wallet transport failed, submitted with GenLayer signer. Waiting...","ok"); rf.value=blankReport(); submitTried.value = false; await sleep(6000); await Promise.all([loadReports(), loadMine()]); toast_("Submitted!","ok"); }
  catch(e) { toast_(errorMessage(e),"err"); }
  finally { submitting.value = false; }
};

const evaluate = async (reportId) => {
  evaluating.value = reportId;
  try { ensureLocalAccount(); const report = reports.value.find(r => r.id === reportId); if (report && !isReportProgramFunded(report)) throw new Error("Fund this program before evaluating payable reports."); const tx = await sb.evaluateReport(reportId); toast_(tx.signer === "browser-wallet" ? "Wallet transaction sent. Waiting for StudioNet..." : "StudioNet wallet transport failed, submitted with GenLayer signer. Waiting...","ok"); await sleep(6000); await Promise.all([loadPrograms(), loadReports(), loadVulns(), loadMine()]); }
  catch(e) { toast_(errorMessage(e),"err"); }
  finally { evaluating.value = ""; }
};

const retryPayout = async (reportId) => {
  retryingPayout.value = reportId;
  try {
    ensureLocalAccount();
    const tx = await sb.retryPayout(reportId);
    toast_(tx.signer === "browser-wallet" ? "Payout retry sent. Waiting for StudioNet..." : "Payout retry submitted. Waiting...", "ok");
    await sleep(6000);
    await Promise.all([loadPrograms(), loadReports(), loadMine()]);
    if (selectedReport.value?.id === reportId) {
      selectedReport.value = reports.value.find(r => r.id === reportId) || selectedReport.value;
    }
  } catch(e) {
    toast_(errorMessage(e), "err");
  } finally {
    retryingPayout.value = "";
  }
};

onMounted(async () => {
  window.ethereum?.on?.("accountsChanged", handleAccountsChanged);
  window.ethereum?.on?.("chainChanged", loadWalletBalance);
  if (evmAddress.value) ensureLocalAccount();
  if (evmAddress.value) await loadWalletBalance();
  await Promise.all([loadPrograms(), loadReports(), loadVulns()]);
  if (evmAddress.value) await loadMine();
  if (sessionStorage.getItem("sb_connect_on_enter") === "true" && !evmAddress.value) {
    sessionStorage.removeItem("sb_connect_on_enter");
    await connect();
  }
});

onBeforeUnmount(() => {
  window.ethereum?.removeListener?.("accountsChanged", handleAccountsChanged);
  window.ethereum?.removeListener?.("chainChanged", loadWalletBalance);
});
</script>
