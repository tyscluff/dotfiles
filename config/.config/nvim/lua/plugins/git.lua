return {
  {
    "sindrets/diffview.nvim",
    cmd = { "DiffviewOpen", "DiffviewClose", "DiffviewToggleFiles", "DiffviewFocusFiles", "DiffviewRefresh" },
    -- We use 'opts' here to pass configuration settings to the plugin
    opts = {
      file_panel = {
        listing_style = "tree", -- Makes it look like a file explorer
        win_config = {
          position = "left",
          width = 35,
        },
      },
      -- This is the specific setting to show untracked files
      enhanced_diff_hl = true,
      hooks = {},
      keymaps = {},
    },
    -- This command ensures untracked files are included when you open the diff
    keys = {
      { "<leader>gv", "<cmd>DiffviewOpen main<cr>", desc = "Diffview Main" },
      {
        "<leader>gV",
        function()
          Snacks.picker.git_branches({
            confirm = function(picker, item)
              picker:close()
              if item then
                vim.cmd("DiffviewOpen " .. item.branch)
              end
            end,
          })
        end,
        desc = "Diffview Branch...",
      },
      { "<leader>gq", "<cmd>DiffviewClose<cr>", desc = "Quit Diffview" },
      { "<leader>gr", "<cmd>DiffviewRefresh<cr>", desc = "Refresh Diffview" },
    },
  },
}
