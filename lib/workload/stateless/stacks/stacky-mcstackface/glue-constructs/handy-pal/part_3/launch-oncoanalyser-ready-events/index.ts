/*
Generate a ready event for the oncoanalyser workflow.

Subscribe to library qc complete -

If given a tumor or normal wgs library - find the complementary library
and check if it is also complete. If both are complete, generate a ready event.

If given a rna library - check if the library is complete.
If it is, generate a ready event.

*/
