using System;
using System.IO;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

public static class VerifySldprtSingleSolid
{
    public static int Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.WriteLine("Usage: verify_sldprt_single_solid.exe final.SLDPRT");
            return 1;
        }

        string finalPart = Path.GetFullPath(args[0]);
        var swType = Type.GetTypeFromProgID("SldWorks.Application", true);
        var sw = (ISldWorks)Activator.CreateInstance(swType);
        sw.Visible = true;

        int errors = 0, warnings = 0;
        var model = sw.OpenDoc6(
            finalPart,
            (int)swDocumentTypes_e.swDocPART,
            (int)swOpenDocOptions_e.swOpenDocOptions_Silent,
            "",
            ref errors,
            ref warnings) as ModelDoc2;
        Console.WriteLine("OPEN_FINAL errors=" + errors + " warnings=" + warnings + " model=" + (model != null));
        if (model == null) return 2;

        var part = model as PartDoc;
        object[] bodies = part == null ? null : part.GetBodies2((int)swBodyType_e.swSolidBody, false) as object[];
        int bodyCount = bodies == null ? 0 : bodies.Length;
        int faceCount = 0;
        int planeFaces = 0;
        int nonPlaneFaces = 0;

        if (bodyCount == 1)
        {
            Body2 body = bodies[0] as Body2;
            faceCount = body == null ? 0 : body.GetFaceCount();
            object[] faces = body == null ? null : body.GetFaces() as object[];
            if (faces != null)
            {
                foreach (object faceObject in faces)
                {
                    Face2 face = faceObject as Face2;
                    Surface surface = face == null ? null : face.GetSurface() as Surface;
                    bool isPlane = false;
                    try { isPlane = surface != null && surface.IsPlane(); } catch { }
                    if (isPlane) planeFaces++; else nonPlaneFaces++;
                }
            }
        }

        Console.WriteLine("FINAL_SOLID_BODIES=" + bodyCount);
        Console.WriteLine("FINAL_FACE_COUNT=" + faceCount);
        Console.WriteLine("FINAL_PLANE_FACES=" + planeFaces);
        Console.WriteLine("FINAL_NONPLANE_FACES=" + nonPlaneFaces);
        Console.WriteLine("VERIFIED_SINGLE_SOLID=" + (bodyCount == 1 && faceCount >= 6));
        try { sw.CloseDoc(model.GetTitle()); } catch { }
        return bodyCount == 1 && faceCount >= 6 ? 0 : 3;
    }
}
