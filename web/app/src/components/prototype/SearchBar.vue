<script setup lang="ts">
// Pill field, green ring, green circular submit — DESIGN-SYSTEM.md §5, measured
// off the live homepage (534x52, borderless 16px input). Blank does not submit
// (010-screens/SPEC.md precedence rule: "empty (blank input) -> no state card,
// the input simply doesn't submit"): submit() itself checks trim() and returns
// early, so no path — click, Enter, or a stray form submit — can POST a blank
// query.
//
// Enter is wired with an EXPLICIT @keydown.enter.prevent, not left to the
// <form>'s native implicit submission (P0, coordinator's browser check,
// 2026-08-07 — typed input, pressed Enter, nothing happened; the identical
// text via the click path worked immediately). The HTML spec's implicit-
// submission rule activates the form's default button on Enter UNLESS that
// button is disabled AT THAT INSTANT — and the button's disabled state here
// is a prop bound through a two-hop v-model round trip (SearchBar ->
// PageHeader -> PrototypePage and back), so it is one Vue render behind the
// raw keystroke that made it non-empty. Click never hits this: you cannot
// click a button that is still disabled. `.prevent` on the keydown suppresses
// the browser's own implicit-submission handling for that same keypress, so
// this does not fire twice.
const props = defineProps<{
  modelValue: string
  placeholder?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [string]
  submit: [string]
}>()

function submit() {
  const value = props.modelValue.trim()
  if (!value) return
  emit('submit', value)
}
</script>

<template>
  <form class="search" @submit.prevent="submit">
    <input
      :value="modelValue"
      type="text"
      :placeholder="placeholder ?? 'Search deals'"
      autocomplete="off"
      @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      @keydown.enter.prevent="submit"
    />
    <button type="submit" class="go" :disabled="!modelValue.trim()" aria-label="Search">
      <svg width="18" height="18" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-linecap="square" stroke-miterlimit="10">
        <circle cx="9" cy="9" r="6" />
        <path d="M13.5 13.5 L17 17" />
      </svg>
    </button>
  </form>
</template>

<style scoped>
.search {
  display: flex;
  align-items: center;
  width: 33.375rem; /* 534px */
  max-width: 100%;
  height: 3.25rem; /* 52px */
  border: 2px solid var(--gp-brand);
  border-radius: var(--gp-radius-pill);
  padding: 0 0.375rem 0 1.25rem;
  background: var(--gp-bg);
}

input {
  flex: 1;
  min-width: 0;
  border: 0;
  outline: 0;
  background: transparent;
  font: inherit;
  font-size: 1rem;
  line-height: 1.625rem;
  color: var(--gp-text);
}

input::placeholder {
  color: var(--gp-text-decorative);
}

.go {
  flex-shrink: 0;
  width: 2.5rem;
  height: 2.5rem;
  border: 0;
  border-radius: var(--gp-radius-pill);
  background: var(--gp-brand);
  color: var(--gp-bg);
  display: grid;
  place-items: center;
  cursor: pointer;
  transition: background var(--gp-duration) var(--gp-ease);
}

.go:hover:not(:disabled) {
  background: var(--gp-brand-hover);
}

.go:disabled {
  background: var(--gp-text-decorative);
  cursor: not-allowed;
}
</style>
