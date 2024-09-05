//! This module is responsible for generating utoipa openapi definitions on top of sea-orm entities.
//! The reason this is required is because sea-orm-cli generates entities with models that are
//! all called `Model`, and this clashes with the utoipa interpretation of schema. Since we only
//! have control over the entities within `filemanager-build` the easiest way to rename entities
//! is here.
//!

use heck::AsPascalCase;
use prettyplease::unparse;
use quote::format_ident;
use std::fs::{read_dir, read_to_string, write};
use std::path::Path;
use syn::visit_mut::VisitMut;
use syn::{parse_file, parse_quote, Ident, ItemStruct};

use crate::error::ErrorKind::OpenAPIGeneration;
use crate::Result;

/// OpenAPI definition generator implementing `VisitMut`.
#[derive(Debug)]
pub struct GenerateOpenAPI<'a> {
    model_ident: &'a Ident,
    name: &'a str,
}

impl<'a> VisitMut for GenerateOpenAPI<'a> {
    fn visit_item_struct_mut(&mut self, i: &mut ItemStruct) {
        if &i.ident == self.model_ident {
            let path_ident: Ident = format_ident!("{}", self.name);
            i.attrs.push(parse_quote! { #[schema(as = #path_ident)] });
        }
    }
}

/// Generate OpenAPI utoipa definitions on top of the sea-orm entities.
pub async fn generate_openapi(out_dir: &Path) -> Result<()> {
    let model_ident: Ident = parse_quote! { Model };
    for path in read_dir(out_dir)? {
        let path = path?.path();
        let content = read_to_string(&path)?;

        let mut tokens = parse_file(&content).map_err(|err| OpenAPIGeneration(err.to_string()))?;
        let stem = path.file_stem().ok_or_else(|| {
            OpenAPIGeneration("expected file with name when generating entities".to_string())
        })?;

        let name = &AsPascalCase(stem.to_string_lossy()).to_string();
        let name = name.trim_end_matches("Object");

        GenerateOpenAPI {
            model_ident: &model_ident,
            name,
        }
        .visit_file_mut(&mut tokens);

        write(path, unparse(&tokens))?;
    }

    Ok(())
}
