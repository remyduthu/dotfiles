-- Set <space> as the leader key.
-- See `:help mapleader`.
-- Must happen before plugins are loaded (otherwise wrong leader will be used).
vim.g.mapleader = " "
vim.g.maplocalleader = " "

-- Sync clipboard between OS and Neovim.
-- Schedule the setting after `UiEnter` because it can increase startup-time.
-- See `:help clipboard`.
vim.schedule(function()
  vim.o.clipboard = "unnamedplus"
end)

-- Case-insensitive searching UNLESS \C or one or more capital letters in the search term.
vim.o.ignorecase = true
vim.o.smartcase = true

-- Clear highlights on search when pressing <Esc> in normal mode.
-- See `:help hlsearch`.
vim.keymap.set("n", "<Esc>", "<cmd>nohlsearch<CR>")
