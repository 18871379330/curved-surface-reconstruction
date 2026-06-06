# SolidWorks Adapter

Use SolidWorks only when the user specifically needs SLDPRT output, SolidWorks visual inspection, or SolidWorks body/face verification.

Requirements:

- Windows;
- SolidWorks installed and licensed;
- local SolidWorks interop DLLs;
- .NET Framework compiler.

Do not bundle proprietary SolidWorks interop DLLs in open-source copies of this skill. Compile scripts by referencing local DLL paths.

Scripts:

- `import_step_verify.cs`: import STEP, save SLDPRT, report body/face counts.
- `verify_sldprt_single_solid.cs`: reopen SLDPRT and verify body/face counts.
