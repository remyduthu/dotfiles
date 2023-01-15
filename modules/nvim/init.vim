set nocompatible

set modelines=0  " https://alioth-lists-archive.debian.net/pipermail/pkg-vim-maintainers/2007-June/004020.html

" http://vimcasts.org/episodes/tabs-and-spaces/
set tabstop=2
set softtabstop=2
set shiftwidth=2
set expandtab

set encoding=utf-8

let mapleader=","

set ignorecase smartcase incsearch showmatch hlsearch
nnoremap <leader><space> :noh<cr>
nnoremap <tab> %
vnoremap <tab> %

noremap <up> <nop>
noremap <down> <nop>
noremap <left> <nop>
noremap <right> <nop>
noremap j gj
noremap k gk
