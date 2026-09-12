import brut.androlib.smali.SmaliBuilder;
import com.android.tools.smali.dexlib2.Opcodes;
import com.android.tools.smali.dexlib2.writer.builder.DexBuilder;
import com.android.tools.smali.dexlib2.writer.io.FileDataStore;
import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.stream.Stream;

/** Assemble a single DEX with the exact SmaliBuilder bundled in Apktool 3.0.3.
 * No resource table, manifest, asset, or native library is rebuilt. */
public final class MeboardSmaliAssembler {
    public static void main(String[] args) throws Exception {
        if (args.length != 3) {
            throw new IllegalArgumentException("usage: <smali-directory> <out.dex> <api-level>");
        }
        Path root = Path.of(args[0]);
        Path output = Path.of(args[1]);
        int api = Integer.parseInt(args[2]);
        List<Path> sources;
        try (Stream<Path> walk = Files.walk(root)) {
            sources = walk.filter(p -> p.toString().endsWith(".smali")).sorted().toList();
        }
        if (sources.isEmpty()) throw new IllegalArgumentException("No smali sources");
        DexBuilder dex = new DexBuilder(new Opcodes(api));
        SmaliBuilder smali = new SmaliBuilder(api);
        for (Path source : sources) {
            if (!smali.buildFile(source.toFile(), dex)) {
                throw new IllegalStateException("Assembly failed: " + source);
            }
        }
        Files.createDirectories(output.toAbsolutePath().getParent());
        dex.writeTo(new FileDataStore(output.toFile()));
        System.out.println("Assembled " + sources.size() + " classes -> " + output);
    }
}
