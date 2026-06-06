using System;
using System.IO;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

public static class SolidWorksImportStepVerify
{
    public static int Main(string[] args)
    {
        if (args.Length < 2)
        {
            Console.WriteLine("Usage: solidworks_import_step_verify.exe input.step output.SLDPRT [preview.png]");
            return 1;
        }

        string stepPath = Path.GetFullPath(args[0]);
        string outPart = Path.GetFullPath(args[1]);
        string preview = args.Length >= 3 ? Path.GetFullPath(args[2]) : null;
        Directory.CreateDirectory(Path.GetDirectoryName(outPart));

        var swType = Type.GetTypeFromProgID("SldWorks.Application", true);
        var sw = (ISldWorks)Activator.CreateInstance(swType);
        sw.Visible = true;

        int errors = 0;
        var model = sw.LoadFile4(stepPath, "", null, ref errors) as ModelDoc2;
        Console.WriteLine("LOADFILE4 errors=" + errors + " model=" + (model != null));
        if (model == null) return 2;

        var part = model as PartDoc;
        object[] bodies = part == null ? null : part.GetBodies2((int)swBodyType_e.swSolidBody, false) as object[];
        int bodyCount = bodies == null ? 0 : bodies.Length;
        int faceCount = 0;
        if (bodyCount == 1)
        {
            Body2 body = bodies[0] as Body2;
            faceCount = body == null ? 0 : body.GetFaceCount();
        }
        Console.WriteLine("SOLID_BODIES=" + bodyCount);
        Console.WriteLine("FACE_COUNT=" + faceCount);

        model.ViewDisplayShaded();
        model.ShowNamedView2("*Isometric", (int)swStandardViews_e.swIsometricView);
        model.ViewZoomtofit2();
        model.GraphicsRedraw2();

        int saveErrors = 0, saveWarnings = 0;
        bool saved = model.Extension.SaveAs(
            outPart,
            (int)swSaveAsVersion_e.swSaveAsCurrentVersion,
            (int)swSaveAsOptions_e.swSaveAsOptions_Silent,
            null,
            ref saveErrors,
            ref saveWarnings);
        Console.WriteLine("SAVE_SLDPRT saved=" + saved + " errors=" + saveErrors + " warnings=" + saveWarnings);

        if (!String.IsNullOrEmpty(preview))
        {
            saveErrors = saveWarnings = 0;
            model.Extension.SaveAs(
                preview,
                (int)swSaveAsVersion_e.swSaveAsCurrentVersion,
                (int)swSaveAsOptions_e.swSaveAsOptions_Silent,
                null,
                ref saveErrors,
                ref saveWarnings);
            Console.WriteLine("PREVIEW " + preview);
        }

        Console.WriteLine("SLDPRT " + outPart);
        try { sw.CloseDoc(model.GetTitle()); } catch { }
        return saved && bodyCount == 1 ? 0 : 3;
    }
}
