using System;
using System.Collections.Generic;
using System.IO;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

public static class BuildNativeLoftCurvedBlock
{
    private static readonly string Workspace = Directory.GetParent(AppDomain.CurrentDomain.BaseDirectory.TrimEnd(Path.DirectorySeparatorChar)).FullName;
    private static readonly string FinalDir = Path.Combine(Workspace, "native_loft_delivery");
    private static readonly string OutPart = Path.Combine(FinalDir, "M1009_curved_face_block_native_loft_v4.SLDPRT");
    private static readonly string OutPreview = Path.Combine(FinalDir, "M1009_curved_face_block_native_loft_v4_preview.png");
    private const double Mm = 0.001;

    public static int Main()
    {
        try
        {
            Directory.CreateDirectory(FinalDir);
            if (File.Exists(OutPart)) File.Delete(OutPart);

            var swType = Type.GetTypeFromProgID("SldWorks.Application", true);
            var sw = (ISldWorks)Activator.CreateInstance(swType);
            sw.Visible = true;

            var model = (ModelDoc2)sw.NewPart();
            if (model == null) throw new InvalidOperationException("Failed to create new SolidWorks part.");
            model.SetTitle2("M1009_curved_face_block_native_loft");

            Feature frontPlane = GetPlane(model, 0);
            if (frontPlane == null) throw new InvalidOperationException("Cannot find front plane.");
            var lofts = new List<Feature>();
            int independentSegments = 0;
            double overlapMm = 0.15;
            for (int i = 0; i < NativeLoftProfileData.SectionCount - 1; i++)
            {
                double leftOffsetMm = NativeLoftProfileData.ProfilesMm[i][0][0] - (i > 0 ? overlapMm : 0.0);
                double rightOffsetMm = NativeLoftProfileData.ProfilesMm[i + 1][0][0] + (i + 1 < NativeLoftProfileData.SectionCount - 1 ? overlapMm : 0.0);
                Feature planeA = CreateOffsetPlane(model, frontPlane, leftOffsetMm, "Plane_Seg_" + i.ToString("00") + "_A");
                Feature planeB = CreateOffsetPlane(model, frontPlane, rightOffsetMm, "Plane_Seg_" + i.ToString("00") + "_B");
                Feature sketchA = CreateClosedProfileSketch(model, planeA, i, leftOffsetMm, "Sketch_Seg_" + i.ToString("00") + "_A");
                Feature sketchB = CreateClosedProfileSketch(model, planeB, i + 1, rightOffsetMm, "Sketch_Seg_" + i.ToString("00") + "_B");
                bool merge = false;
                Feature loft = CreateLoftBetween(model, sketchA, sketchB, i, merge);
                if (loft == null && merge)
                {
                    Console.WriteLine("MERGE_SEGMENT_FAILED_TRY_INDEPENDENT " + i);
                    loft = CreateLoftBetween(model, sketchA, sketchB, i, false);
                    independentSegments++;
                }
                if (loft == null) throw new InvalidOperationException("Segment loft failed between sections " + i + " and " + (i + 1));
                loft.Name = "LoftBoss_Segment_" + i.ToString("00");
                lofts.Add(loft);
                bool suppressed = loft.SetSuppression2(
                    (int)swFeatureSuppressionAction_e.swSuppressFeature,
                    (int)swInConfigurationOpts_e.swAllConfiguration,
                    null);
                Console.WriteLine("SUPPRESS_SEGMENT " + i + " " + suppressed);
                model.EditRebuild3();
            }

            for (int i = 0; i < lofts.Count; i++)
            {
                bool unsuppressed = lofts[i].SetSuppression2(
                    (int)swFeatureSuppressionAction_e.swUnSuppressFeature,
                    (int)swInConfigurationOpts_e.swAllConfiguration,
                    null);
                Console.WriteLine("UNSUPPRESS_SEGMENT " + i + " " + unsuppressed);
            }
            model.EditRebuild3();
            TryCombineBodies(model);

            model.ViewDisplayShaded();
            model.ShowNamedView2("*Isometric", (int)swStandardViews_e.swIsometricView);
            model.ViewZoomtofit2();
            model.GraphicsRedraw2();

            int errors = 0, warnings = 0;
            bool saved = model.Extension.SaveAs(
                OutPart,
                (int)swSaveAsVersion_e.swSaveAsCurrentVersion,
                (int)swSaveAsOptions_e.swSaveAsOptions_Silent,
                null,
                ref errors,
                ref warnings);
            Console.WriteLine("SAVE_PART saved=" + saved + " errors=" + errors + " warnings=" + warnings);
            if (!saved) throw new InvalidOperationException("Failed to save native loft part.");

            errors = warnings = 0;
            model.Extension.SaveAs(
                OutPreview,
                (int)swSaveAsVersion_e.swSaveAsCurrentVersion,
                (int)swSaveAsOptions_e.swSaveAsOptions_Silent,
                null,
                ref errors,
                ref warnings);

            var part = model as PartDoc;
            var bodies = part == null ? null : part.GetBodies2((int)swBodyType_e.swSolidBody, false) as object[];
            Console.WriteLine("SOLID_BODIES=" + (bodies == null ? 0 : bodies.Length));
            Console.WriteLine("LOFT_SEGMENTS=" + lofts.Count);
            Console.WriteLine("INDEPENDENT_SEGMENTS=" + independentSegments);
            Console.WriteLine("SLDPRT " + OutPart);
            return 0;
        }
        catch (Exception ex)
        {
            Console.WriteLine("EXCEPTION " + ex.GetType().FullName + " " + ex.Message);
            Console.WriteLine(ex.StackTrace);
            return 99;
        }
    }

    private static Feature CreateOffsetPlane(ModelDoc2 model, Feature frontPlane, double offsetMm, string name)
    {
        double offset = offsetMm * Mm;
        if (Math.Abs(offset) < 1e-9) return frontPlane;
        model.ClearSelection2(true);
        frontPlane.Select2(false, 0);
        Feature plane = model.FeatureManager.InsertRefPlane(
            (int)swRefPlaneReferenceConstraints_e.swRefPlaneReferenceConstraint_Distance,
            offset, 0, 0, 0, 0) as Feature;
        if (plane == null)
        {
            throw new InvalidOperationException("Failed to create offset plane " + name);
        }
        plane.Name = name;
        return plane;
    }

    private static Feature GetPlane(ModelDoc2 model, int index)
    {
        var planes = new List<Feature>();
        Feature feature = model.FirstFeature() as Feature;
        while (feature != null)
        {
            try
            {
                if (feature.GetTypeName2() == "RefPlane") planes.Add(feature);
            }
            catch { }
            feature = feature.GetNextFeature() as Feature;
        }
        Console.WriteLine("DEFAULT_PLANES=" + planes.Count);
        for (int i = 0; i < planes.Count; i++) Console.WriteLine("PLANE_" + i + "=" + planes[i].Name);
        return planes.Count > index ? planes[index] : null;
    }

    private static Feature CreateClosedProfileSketch(ModelDoc2 model, Feature plane, int sectionIndex, double overrideOffsetMm, string name)
    {
        double[][] profile = NativeLoftProfileData.ProfilesMm[sectionIndex];
        int n = profile.Length;
        double sectionOffset = overrideOffsetMm * Mm;
        double widthMin = profile[0][1] * Mm;
        double widthMax = profile[n - 1][1] * Mm;
        double heightStart = profile[0][2] * Mm;
        double heightEnd = profile[n - 1][2] * Mm;
        double backHeight = 0.0;

        model.ClearSelection2(true);
        plane.Select2(false, 0);
        model.SketchManager.InsertSketch(true);
        model.SketchManager.DisplayWhenAdded = false;

        model.SketchManager.CreateLine(widthMin, backHeight, sectionOffset, widthMin, heightStart, sectionOffset);

        double[] splineData = new double[n * 3];
        for (int i = 0; i < n; i++)
        {
            splineData[i * 3 + 0] = profile[i][1] * Mm;
            splineData[i * 3 + 1] = profile[i][2] * Mm;
            splineData[i * 3 + 2] = sectionOffset;
        }
        model.SketchManager.CreateSpline2(splineData, true);

        model.SketchManager.CreateLine(widthMax, heightEnd, sectionOffset, widthMax, backHeight, sectionOffset);
        model.SketchManager.CreateLine(widthMax, backHeight, sectionOffset, widthMin, backHeight, sectionOffset);

        Sketch activeSketch = model.SketchManager.ActiveSketch as Sketch;
        if (activeSketch != null)
        {
            activeSketch.MergePoints(0.00002);
            Console.WriteLine("SKETCH_CONTOURS_BEFORE_EXIT " + name + " " + activeSketch.GetSketchContourCount());
        }

        model.SketchManager.DisplayWhenAdded = true;
        model.SketchManager.InsertSketch(true);
        model.ClearSelection2(true);

        Feature sketch = model.FeatureByPositionReverse(0) as Feature;
        if (sketch == null) throw new InvalidOperationException("Cannot get created sketch " + name);
        sketch.Name = name;
        Sketch createdSketch = sketch.GetSpecificFeature2() as Sketch;
        if (createdSketch != null) Console.WriteLine("SKETCH_CONTOURS " + name + " " + createdSketch.GetSketchContourCount());
        return sketch;
    }

    private static Feature CreateLoftBetween(ModelDoc2 model, Feature a, Feature b, int index, bool merge)
    {
        model.ClearSelection2(true);
        bool okA = model.Extension.SelectByID2(a.Name, "SKETCH", 0, 0, 0, false, 0, null, 0);
        bool okB = model.Extension.SelectByID2(b.Name, "SKETCH", 0, 0, 0, true, 0, null, 0);
        Console.WriteLine("SELECT_SEGMENT_SKETCHES " + index + " " + okA + " " + okB + " merge=" + merge);
        if (!okA || !okB) return null;

        Feature loft = model.FeatureManager.InsertProtrusionBlend2(
            false, false, false, 1.0,
            0, 0,
            0.0, 0.0,
            false, false,
            false,
            0.0, 0.0,
            0,
            merge, false, false,
            0) as Feature;
        if (loft != null) return loft;

        Console.WriteLine("SEGMENT_LOFT2_FAILED_TRY_TANGENT " + index);
        model.ClearSelection2(true);
        model.Extension.SelectByID2(a.Name, "SKETCH", 0, 0, 0, false, 0, null, 0);
        model.Extension.SelectByID2(b.Name, "SKETCH", 0, 0, 0, true, 0, null, 0);
        loft = model.FeatureManager.InsertProtrusionBlend2(
            false, true, false, 1.0,
            0, 0,
            1.0, 1.0,
            true, true,
            false,
            0.0, 0.0,
            0,
            merge, true, true,
            0) as Feature;
        return loft;
    }

    private static void TryCombineBodies(ModelDoc2 model)
    {
        var part = model as PartDoc;
        if (part == null) return;
        object[] bodies = part.GetBodies2((int)swBodyType_e.swSolidBody, false) as object[];
        Console.WriteLine("BODIES_BEFORE_COMBINE=" + (bodies == null ? 0 : bodies.Length));
        if (bodies == null || bodies.Length <= 1) return;

        try
        {
            model.ClearSelection2(true);
            for (int i = 0; i < bodies.Length; i++)
            {
                Body2 body = bodies[i] as Body2;
                if (body != null)
                {
                    bool ok = body.Select(i > 0, 0);
                    Console.WriteLine("SELECT_BODY_FOR_COMBINE " + i + " " + ok);
                }
            }
            Feature combined = model.FeatureManager.InsertCombineFeature(
                (int)swCombineBodiesOperationType_e.swCombineBodiesOperationAdd,
                null,
                null) as Feature;
            Console.WriteLine("COMBINE_FEATURE=" + (combined != null));
            if (combined != null) combined.Name = "Combine_Add_All_LoftSegments";
        }
        catch (Exception ex)
        {
            Console.WriteLine("COMBINE_EXCEPTION " + ex.GetType().FullName + " " + ex.Message);
        }
    }
}
