return {
  {
    "mfussenegger/nvim-lint",
    config = function()
      require("lint").linters_by_ft = {
        go = { "golangcilint" },
      }
    end,
  },
  {
    "williamboman/mason.nvim",
    config = function()
      require("mason").setup()
    end,
  },
  {
    "williamboman/mason-lspconfig.nvim",
    config = function()
      require("mason-lspconfig").setup({
        ensure_installed = { "lua_ls", "gopls" },
      })
    end,
  },
  {
    "WhoIsSethDaniel/mason-tool-installer.nvim",
    config = function()
      require("mason-tool-installer").setup({
        ensure_installed = {
          "intelephense",
          "lua_ls",
          "prettier",
          "stylua",
          "shellcheck",
          "gopls",
          "golangci-lint",
          "gofumpt",
          "golines",
        },
      })
    end,
  },
  {
    "neovim/nvim-lspconfig",
    config = function()
      local capabilities = require("cmp_nvim_lsp").default_capabilities()

      local config = require("lspconfig")
      config.lua_ls.setup({
        capabilities = capabilities,
        settings = {
          Lua = {
            diagnostics = {
              globals = { "vim" },
            },
          },
        },
      })

      config.gopls.setup({ capabilities = capabilities })

      config.ts_ls.setup({ capabilities = capabilities })
    end,
  },
  {
    "stevearc/conform.nvim",
    config = function()
      require("conform").setup({
        formatters_by_ft = {
          go = { "gofumpt", "golines" },
          lua = { "stylua" },
          ["_"] = { "prettier" },
        },
        format_on_save = {},
      })
    end,
  },
}
