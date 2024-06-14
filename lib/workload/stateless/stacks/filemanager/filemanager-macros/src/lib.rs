use proc_macro::TokenStream;
use std::env::var;
use syn::{Ident, Lit, LitStr, parse_macro_input, Visibility};
use syn::__private::quote::quote;
use syn::__private::Span;
use syn::parse::{Parse, ParseStream};

struct ModulePath {
    visibility: Visibility,
    name: Ident,
    path: Lit,
}

impl Parse for ModulePath {
    fn parse(input: ParseStream) -> syn::Result<Self> {
        let visibility: Visibility = input.parse()?;
        let name: Ident = input.parse()?;
        let path: Lit = input.parse()?;

        Ok(ModulePath {
            visibility,
            name,
            path
        })
    }
}

#[proc_macro]
pub fn mod_path(input: TokenStream) -> TokenStream {


    let ModulePath {
        visibility,
        name,
        path
    } = parse_macro_input!(input as ModulePath);

    let dir = var("OUT_DIR").unwrap() + "/mod.rs";
    let path = LitStr::new(&dir, Span::call_site());
    quote!(
        #[path = #path]
        #visibility mod #name;
    ).into()
}