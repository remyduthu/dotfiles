vim.keymap.set("n", "gd", "<cmd>lua vim.lsp.buf.definition()<CR>", { noremap = true, silent = true })
vim.keymap.set("n", "K", "<cmd>lua vim.lsp.buf.hover()<CR>", { noremap = true, silent = true })
