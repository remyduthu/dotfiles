-- https://github.com/nvim-tree/nvim-tree.lua/wiki/Installation
return {
  "nvim-tree/nvim-tree.lua",
  dependencies = {
    "nvim-tree/nvim-web-devicons",
  },
  version = "*",
  lazy = false,
  config = function()
    require("nvim-tree").setup({
      disable_netrw = true,
      git = {
        enable = true,
        ignore = true,
      },
      update_focused_file = { enable = true },
      renderer = {
        icons = {
          show = {
            file = false,
            folder = false,
            folder_arrow = false,
            git = false,
          },
        },
      },
      view = {
        side = "right",
      },
    })
  end,
}
