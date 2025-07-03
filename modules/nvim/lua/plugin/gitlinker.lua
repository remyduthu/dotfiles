return {
  "ruifm/gitlinker.nvim",
  dependencies = { "nvim-lua/plenary.nvim" },
  config = function()
    require("gitlinker").setup({
      opts = {
        mappings = "<leader>gy",
      },
      callbacks = {
        ["github.com"] = require("gitlinker.hosts").get_github_type_url,
        ["gitlab.com"] = require("gitlinker.hosts").get_gitlab_type_url,
      },
    })
  end,
}
