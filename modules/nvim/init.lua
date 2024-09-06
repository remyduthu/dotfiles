vim.opt.compatible = false

-- Reference: https://alioth-lists-archive.debian.net/pipermail/pkg-vim-maintainers/2007-June/004020.html
vim.opt.modelines = 0

-- Reference: http://vimcasts.org/episodes/tabs-and-spaces/
vim.opt.tabstop = 2
vim.opt.softtabstop = 2
vim.opt.shiftwidth = 2
vim.opt.expandtab = true

vim.opt.number = true
vim.opt.relativenumber = true

vim.opt.encoding = 'utf-8'

vim.opt.ignorecase = true
vim.opt.incsearch = true
vim.opt.showmatch = true
vim.opt.hlsearch = true

vim.g.mapleader = " "
vim.g.maplocalleader = " "

vim.keymap.set('n', '<leader><space>', ':noh<CR>')

vim.keymap.set('n', '<tab>', '%')
vim.keymap.set('v', '<tab>', '%')

vim.opt.scrolloff = 4

-- Center the screen when moving screen.
vim.keymap.set('n', '<C-d>', '<C-d>zz')
vim.keymap.set('n', '<C-u>', '<C-u>zz')

vim.keymap.set('n', '<up>', '<nop>')
vim.keymap.set('n', '<down>', '<nop>')
vim.keymap.set('n', '<left>', '<nop>')
vim.keymap.set('n', '<right>', '<nop>')
vim.keymap.set('n', 'j', 'gj')
vim.keymap.set('n', 'k', 'gk')

-- Center the screen when navigating search results.
vim.keymap.set('n', 'n', 'nzz')
vim.keymap.set('n', 'N', 'Nzz')
