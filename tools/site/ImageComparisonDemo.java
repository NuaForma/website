import dev.nuaforma.image.comparison.ImageComparison;
import dev.nuaforma.image.comparison.model.ImageComparisonResult;
import dev.nuaforma.image.comparison.model.Rectangle;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.nio.file.*;
import java.util.List;
import java.util.Locale;
import javax.imageio.ImageIO;

/** Fixed, synthetic website example; the library produces the actual difference images. */
public final class ImageComparisonDemo {
    private static final Color INK = new Color(20, 43, 54);
    private static final Color TEAL = new Color(0, 126, 131);

    private static BufferedImage document(boolean changed) {
        BufferedImage image = new BufferedImage(640, 500, BufferedImage.TYPE_INT_RGB);
        Graphics2D g = image.createGraphics();
        try {
            g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            g.setColor(Color.WHITE); g.fillRect(0, 0, 640, 500);
            g.setColor(TEAL); g.fillRoundRect(36, 32, 30, 30, 8, 8);
            g.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 20)); g.drawString("NuaForma", 78, 55);
            g.setColor(INK); g.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 36)); g.drawString("Project summary", 36, 120);
            g.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 18));
            g.drawString("NF-005  /  Prepared for Ada", 36, 153);
            g.drawString(changed ? "25 Oct 2026" : "18 Oct 2026", 450, 153);
            g.setColor(new Color(233, 243, 240)); g.fillRect(36, 190, 568, 44);
            g.setColor(INK); g.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 18));
            g.drawString("Deliverable", 50, 219); g.drawString("Amount", 480, 219);
            g.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 20));
            g.drawString("Template design", 50, 270); g.drawString("EUR 800", 480, 270);
            g.drawString("Document delivery", 50, 320); g.drawString(changed ? "EUR 450" : "EUR 400", 480, 320);
            g.setColor(new Color(216, 226, 223)); g.drawLine(36, 345, 604, 345);
            g.setColor(INK); g.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 23));
            g.drawString("Total", 50, 390); g.drawString(changed ? "EUR 1,250" : "EUR 1,200", 450, 390);
            g.setColor(TEAL); g.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 17));
            g.drawString("A fixed image. A deliberate change.", 36, 457);
        } finally { g.dispose(); }
        return image;
    }

    public static void main(String[] args) throws Exception {
        Path output = Path.of(args[0]); Files.createDirectories(output);
        BufferedImage expected = document(false), actual = document(true);
        ImageIO.write(expected, "png", output.resolve("expected.png").toFile());
        ImageIO.write(actual, "png", output.resolve("actual.png").toFile());
        StringBuilder metadata = new StringBuilder("{\n  \"version\": \"5.0.0\",\n  \"cases\": {\n");
        for (boolean exclude : new boolean[]{false, true}) {
            ImageComparison comparison = new ImageComparison(document(false), document(true))
                .setPixelToleranceLevel(0.1).setThreshold(5).setRectangleLineWidth(3)
                .setDifferenceRectangleColor(new Color(206, 47, 68));
            if (exclude) comparison.setExcludedAreas(List.of(new Rectangle(435, 128, 610, 166))).setDrawExcludedRectangles(true);
            ImageComparisonResult result = comparison.compareImages();
            if (!result.getImageComparisonState().name().equals("MISMATCH")) throw new IllegalStateException("Expected real differences");
            String key = exclude ? "exclude-date" : "all-pixels";
            result.writeResultTo(output.resolve(key + ".png").toFile());
            metadata.append(String.format(Locale.ROOT,
                "    \"%s\": {\"state\": \"MISMATCH\", \"regions\": %d, \"differencePercent\": %.8f}%s\n",
                key, result.getRectangles().size(), result.getDifferencePercent(), exclude ? "" : ","));
        }
        Files.writeString(output.resolve("comparison.json"), metadata + "  }\n}\n");
    }
}
