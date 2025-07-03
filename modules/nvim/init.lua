vim.g.loaded_netrw = 1
vim.g.loaded_netrwPlugin = 1

require("remyduthu")

vim.opt.fillchars:append("eob: ")

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

vim.opt.encoding = "utf-8"

vim.opt.ignorecase = true
vim.opt.incsearch = true
vim.opt.showmatch = true
vim.opt.hlsearch = true
