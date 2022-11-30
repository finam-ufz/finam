import io
import os
import pstats


def _convert_to_csv(in_path, out_path):
    result = io.StringIO()

    pstats.Stats(in_path, stream=result).print_stats()
    result = result.getvalue()
    result = "ncalls" + result.split("ncalls")[-1]
    result = "\n".join(
        [",".join(line.rstrip().split(None, 5)) for line in result.split("\n")]
    )
    with open(out_path, "w+") as f:
        f.write(result)
        f.close()


if __name__ == "__main__":
    path = "prof/"
    for file in os.listdir(path):
        if file.endswith(".pstats"):
            in_file = os.path.join(path, file)
            out_file = os.path.join(path, file.replace(".pstats", ".csv"))
            _convert_to_csv(in_file, out_file)
