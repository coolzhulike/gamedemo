# Mounted-world source archive (2026-10-16)

This initial archive preserves four existing text files from the mounted-world prototype: the mounted actor, world integration script, scene entry point, and original usage notes. The source bytes are unchanged.

This is an incremental code archive, not a standalone game or a complete project backup. It still requires the compatible Godot world project, inn/world scripts, and horse/rider assets referenced by the scripts. Those binary assets are not included in this initial archive; their distribution rights require separate review.

To restore these files, copy the contents of `world_mounted_r01/private_mounted/` into `private_mounted/` within the matching Godot project. See the original Chinese README for its controls and known limitations. Historical test claims in that README describe the original project session, not a new test of this partial archive.

`manifest.json` records the original relative source paths, byte sizes, SHA-256 values, and Git blob hashes. Verify those values after downloading before relying on this archive. This initial commit alone is not grounds to discard the complete local project.
