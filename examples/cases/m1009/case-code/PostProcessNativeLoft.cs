using System;
using System.IO;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

public static class PostProcessNativeLoft
{
    private static readonly string Workspace = Directory.GetParent(AppDomain.CurrentDomain.BaseDirectory.TrimEnd(Path.DirectorySeparatorChar)).FullName;
    private static readonly string FinalDir = Path.Combine(Workspace, "native_loft_delivery");
    private static readonly string SourcePart = Path.Combine(FinalDir, "M1009_curved_face_block_native_loft_v4.SLDPRT");
    private static readonly string OutPart = Path.Combine(FinalDir, "M1009_curved_face_block_native_loft_clean.SLDPRT");
    private static readonly string OutPreview = Path.Combine(FinalDir, "M1009_curved_face_block_native_loft_clean_preview.png");

    public static int Main()
    {
        try
        {
            var swType = Type.GetTypeFromProgID("SldWorks.Application", true);
            var sw = (ISldWorks)Activator.CreateInstance(swType);
            sw.Visible = true;

            int errors = 0, warnings = 0;
            var model = (ModelDoc2)sw.OpenDoc6(
                SourcePart,
                (int)swDocumentTypes_e.swDocPART,
                (int)swOpenDocOptions_e.swOpenDocOptions_Silent,
                "",
                ref errors,
                ref warnings);
            Console.WriteLine("OPEN_PART errors=" + errors + " warnings=" + warnings);
            if (model == null) throw new InvalidOperationException("Failed to open native loft part.");

            TryCombine(model);
            HideReferenceFeatures(model);
            HideDisplayReferenceItems(model);

            model.ViewDisplayShaded();
            model.ShowNamedView2("*Isometric", (int)swStandardViews_e.swIsometricView);
            model.ViewZoomtofit2();
            model.GraphicsRedraw2();

            errors = warnings = 0;
            bool saved = model.Extension.SaveAs(
                OutPart,
                (int)swSaveAsVersion_e.swSaveAsCurrentVersion,
                (int)swSaveAsOptions_e.swSaveAsOptions_Silent,
                null,
                ref errors,
                ref warnings);
            Console.WriteLine("SAVE_PART saved=" + saved + " errors=" + errors + " warnings=" + warnings);

            errors = warnings = 0;
            model.Extension.SaveAs(
                OutPreview,
                (int)swSaveAsVersion_e.swSaveAsCurrentVersion,
                (int)swSaveAsOptions_e.swSaveAsOptions_Silent,
                null,
                ref errors,
                ref warnings);

            var part = model as PartDoc;
            object[] bodies = part == null ? null : part.GetBodies2((int)swBodyType_e.swSolidBody, false) as object[];
            Console.WriteLine("SOLID_BODIES_FINAL=" + (bodies == null ? 0 : bodies.Length));
            Console.WriteLine("SLDPRT " + OutPart);
            return saved ? 0 : 2;
        }
        catch (Exception ex)
        {
            Console.WriteLine("EXCEPTION " + ex.GetType().FullName + " " + ex.Message);
            Console.WriteLine(ex.StackTrace);
            return 99;
        }
    }

    private static void TryCombine(ModelDoc2 model)
    {
        var part = model as PartDoc;
        if (part == null) return;
        object[] bodies = part.GetBodies2((int)swBodyType_e.swSolidBody, false) as object[];
        Console.WriteLine("BODIES_BEFORE_POST_COMBINE=" + (bodies == null ? 0 : bodies.Length));
        if (bodies == null || bodies.Length <= 1) return;

        try
        {
            Body2 main = bodies[0] as Body2;
            object[] tools = new object[bodies.Length - 1];
            for (int i = 1; i < bodies.Length; i++) tools[i - 1] = bodies[i];
            Feature combined = model.FeatureManager.InsertCombineFeature(
                (int)swCombineBodiesOperationType_e.swCombineBodiesOperationAdd,
                main,
                tools) as Feature;
            Console.WriteLine("POST_COMBINE_MAIN_TOOL=" + (combined != null));
            if (combined != null)
            {
                combined.Name = "Combine_Add_All_LoftSegments";
                model.EditRebuild3();
                return;
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine("POST_COMBINE_MAIN_TOOL_EXCEPTION " + ex.GetType().FullName + " " + ex.Message);
        }

        try
        {
            model.ClearSelection2(true);
            for (int i = 0; i < bodies.Length; i++)
            {
                Body2 body = bodies[i] as Body2;
                if (body != null) body.Select(i > 0, 0);
            }
            Feature combined = model.FeatureManager.InsertCombineFeature(
                (int)swCombineBodiesOperationType_e.swCombineBodiesOperationAdd,
                null,
                null) as Feature;
            Console.WriteLine("POST_COMBINE_SELECTED=" + (combined != null));
            if (combined != null) combined.Name = "Combine_Add_All_LoftSegments";
            model.EditRebuild3();
        }
        catch (Exception ex)
        {
            Console.WriteLine("POST_COMBINE_SELECTED_EXCEPTION " + ex.GetType().FullName + " " + ex.Message);
        }
    }

    private static void HideReferenceFeatures(ModelDoc2 model)
    {
        Feature feature = model.FirstFeature() as Feature;
        int hidden = 0;
        while (feature != null)
        {
            string typeName = "";
            try { typeName = feature.GetTypeName2(); } catch { }
            string name = "";
            try { name = feature.Name ?? ""; } catch { }
            if (typeName == "RefPlane" || typeName == "ProfileFeature" || name.StartsWith("Plane_") || name.StartsWith("Sketch_"))
            {
                try
                {
                    feature.Select2(false, 0);
                    model.BlankRefGeom();
                    model.ClearSelection2(true);
                    hidden++;
                }
                catch { }
            }
            feature = feature.GetNextFeature() as Feature;
        }
        Console.WriteLine("HIDDEN_REF_FEATURES=" + hidden);
    }

    private static void HideDisplayReferenceItems(ModelDoc2 model)
    {
        try { model.SetUserPreferenceToggle((int)swUserPreferenceToggle_e.swDisplayPlanes, false); } catch { }
        try { model.SetUserPreferenceToggle((int)swUserPreferenceToggle_e.swDisplaySketches, false); } catch { }
        try { model.SetUserPreferenceToggle((int)swUserPreferenceToggle_e.swDisplayCurves, false); } catch { }
        try { model.SetUserPreferenceToggle((int)swUserPreferenceToggle_e.swDisplayReferencePoints, false); } catch { }
        try { model.SetUserPreferenceToggle((int)swUserPreferenceToggle_e.swShowRefGeomName, false); } catch { }
    }
}
