use darling::{Error, FromMeta};
use darling::ast::NestedMeta;
use syn::ItemFn;
use proc_macro::TokenStream;
use quote::{format_ident, quote};

#[derive(Debug, FromMeta)]
struct MacroArgs {
}

#[proc_macro_attribute]
pub fn import_plrust_function(args: TokenStream, input: TokenStream) -> TokenStream {
    let attr_args = match NestedMeta::parse_meta_list(args.into()) {
        Ok(v) => v,
        Err(e) => { return TokenStream::from(Error::from(e).write_errors()); }
    };
    let args = match MacroArgs::from_list(&attr_args) {
        Ok(v) => v,
        Err(e) => { return TokenStream::from(e.write_errors()); }
    };

    let input = syn::parse_macro_input!(input as ItemFn);

    let input_clone = input.clone();
    let vis = input_clone.vis;
    let name = format_ident!("{}_migrate", input_clone.sig.ident);

    let method = quote! {
        #vis fn #name() -> sqlx::migrate::Migrator {
            todo!();
        }
    };

    let tokens = quote! {
        #input
        #method
    };

    tokens.into()
}