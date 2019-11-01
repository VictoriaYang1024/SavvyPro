import os
import subprocess
import csv
import time
import logging.handlers
import shlex

start = time.time()

def set_logger(logger_name, log_file, level = logging.INFO):
    logger = logging.getLogger(logger_name)
    format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    logger_info = logging.FileHandler(log_file,mode="w")
    logger_info.setFormatter(format)
    logger_error = logging.FileHandler(log_file,mode="w")
    logger_error.setFormatter(format)

    logger.setLevel(level)
    logger.addHandler(logger_info)
    logger.addHandler(logger_error)


def main(file):
    res = process_probe(file)
    if res == 1:
        return
    handle(res)
    print("Completed! Check video_info.csv")

def process_probe(file):
    proc = subprocess.Popen(['ffprobe', file],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    res = proc.communicate()[0]
    if 'Invalid data found when processing input' in res:
        logger_error.error("This file is broken" + " duration: " + str(time.time() - start))
        print("The file is broken or missing some data, we cannot process it")
        return 1
    if 'No such file or directory' in res:
        logger_info.warning("Cannot found the file" + " duration: " + str(time.time() - start))
        print("Cannot find the file")
        return 1
    return res

def convertMP4(file):
    lst = file.split(".")
    cmd = ["ffmpeg", "-i", file, "-q:v", "0", lst[0] +".mp4"]
    subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

def handle(doc):
    doc_lst = doc.split("\n")
    flag1 = False
    flag2 = False
    flagv = "f"
    with open("video_info.csv", "wb") as csvfile:
        logger_info.info("open video_info.csc" + " Duration: " + str(time.time() - start))
        writer = csv.writer(csvfile)

        cmd = "ffprobe -v error -select_streams v:0 -show_entries " \
              "stream=codec_name,width,height,bit_rate -of default=noprint_wrappers=1:nokey=1"
        proc1 = subprocess.Popen(shlex.split(cmd) + [file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stream_info = proc1.communicate()[0].split("\n")
        writer.writerow(["codecs: " + stream_info[0]])
        logger_info.info("write codecs to .csv filr" + " Duration: " + str(time.time() - start))
        writer.writerow(["resolution: " + stream_info[1] + " px width " + stream_info[2] + " px height"])
        logger_info.info("write resolution to .csv filr" + " Duration: " + str(time.time() - start))
        writer.writerow(["vedio bit_rate: " + str(int(stream_info[3])//1000) + " kb/s"])
        logger_info.info("write vedio bit_rate to .csv filr" + " Duration: " + str(time.time() - start))

        for line in doc_lst:
            if line.strip().startswith("Duration:"):
                duration_lst = line.strip().split(", ")
                duration = duration_lst[0].replace('.', ':').split(":")
                bitrate = duration_lst[-1]
                duration_format = duration[1] + " hr " + duration[2] + " min " \
                                  + duration[3] + " sec " + duration[4] + " ms "
                writer.writerow(["duration: " + duration_format])
                logger_info.info("write duration of vedio to .csv filr" + " Duration: " + str(time.time() - start))
                writer.writerow(["file bit_rate: " + bitrate])
                logger_info.info("write file_bitrate to .csv filr" + " Duration: " + str(time.time() - start))
            if line.strip().startswith("Stream #"):
                if "Video" in line:
                    flagv = "v"
            if line.strip().startswith("encoder"):
                encoder = line.strip().split(": ")
                if len(encoder) != 2:
                    if flagv == "f":
                        writer.writerow(["No file encoder info"])
                        logger_info.warning("No file encoder info" + " Duration: " + str(time.time() - start))
                        flag1 = True
                    if flagv == "v":
                        writer.writerow(["No video encoder info"])
                        logger_info.warning("No video encoder info" + " Duration: " + str(time.time() - start))
                        flag2 = True
                else:
                    if flagv == "f":
                        writer.writerow(["file_encoder: " + encoder[1]])
                        logger_info.info("write file_encoder to .csv filr" + " Duration: " + str(time.time() - start))
                        flag1 = True
                    if flagv == "v":
                        writer.writerow(["video_encoder: " + encoder[1]])
                        logger_info.info("write video_encoder to .csv filr" + " Duration: " + str(time.time() - start))
                        flag2 = True
        if not flag1:
            writer.writerow(["There is no file encoder"])
            logger_info.warning("There is no file encoder" + " Duration: " + str(time.time() - start))
        if not flag2:
            writer.writerow(["There is no video encoder"])
            logger_info.warning("There is no video encoder" + " Duration: " + str(time.time() - start))

    csvfile.close()
    logger_info.info("video_info.csv is closed" + " Duration: " + str(time.time() - start))
    return

def check_file():
    flag = False
    file = raw_input("Enter a .mp4/mov file : ")
    while not flag:
        if os.path.splitext(file)[1] == ".mp4":
            flag = True
            res = process_probe(file)
            if res == 1:
                return 1
            logger_info.info("People upload a .mp4/mov file" + " Duration: " + str(time.time() - start))
        elif os.path.splitext(file)[1] == ".mov":
            res = process_probe(file)
            if res == 1:
                return 1
            flag = True
            lst = file.split(".")
            get = raw_input("This is a .mov file, convert it to .mp4?(y/n)")
            if get == "y":
                convertMP4(file)
                print("processing, wait 30 secs....")
                time.sleep(40)
                file = lst[0] + ".mp4"
                logger_info.info("The file is .mov, change to .mp4 file" + " Duration: " + str(time.time() - start))
            else:
                print("process .mov now")

        else:
            file = raw_input("This file is not .mp4/mov file, please enter a .mp4/mov file : ")
            logger_info.warning("People do not upload mp4/mov file" + " Duration: " + str(time.time() - start))
    return file

if __name__ == "__main__":
    set_logger('logger_info', 'info.log')
    set_logger('logger_error', 'error.log')
    logger_info = logging.getLogger('logger_info')
    logger_error = logging.getLogger('logger_error')
    file = check_file()
    if file != 1:
        main(file)

