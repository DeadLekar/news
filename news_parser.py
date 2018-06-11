import os
import re
import sqlite3 as lite
from datetime import *
import pandas
import numpy as np
import serviceFunctions as sf

class Text:
    DATES = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря', 'года', 'г.', '']
    QUANTS = ['тыс', 'млн', 'миллион', 'млрд', 'миллиард', 'трлн', 'триллион']
    txt = ''
    public_date = ''
    public_time = ''
    source = ''
    names = []
    conn = None

    def __init__(self, _path, _conn=None, _rbc=None, _id=None, enc='utf-8'):
        """
        reads text file
        :param path: path to text file
        :param c: coursor to news.db
        """
        self.conn = _conn
        self.rbc = (_rbc == 1)
        self.id = _id
        self.path = _path
        self.header = ''
        self.txt = ''
        body_exp = re.compile(r'Body:(.*)')
        cat_exp = re.compile(r'^Category: (.+)')
        header_exp = re.compile(r'^Header: (.+)')

        enc_arr = ['cp1251', 'utf-8']
        lines = []
        for enc in enc_arr:
            file = open(_path, 'r', encoding=enc)
            try:
                lines = file.readlines()
                flg_wrong = False
                for line in lines:
                    if chr(176) in line:
                        flg_wrong = True
                        break
                if not flg_wrong:
                    file.close()
                    break
            except:
                pass

        if lines:
            if not _rbc:
                flg_body = False
                for line in lines:
                    cat_match = re.match(cat_exp, line)
                    if cat_match:
                        self.source = cat_match.group(1)

                    header_match = re.match(header_exp, line)
                    if header_match:
                        self.header = header_match.group(1)

                    if flg_body:
                        self.txt += line
                    else:
                        body_match = re.match(body_exp, line)
                        if body_match:
                            flg_body = True
            else:
                for line in lines:
                    line = sf.clear_string(line, sf.rus_letters+sf.lat_letters+sf.digits+sf.puncts+' ')
                    if line:
                        self.header = line
                        break
                self.txt = ''.join(lines)
                self.source = 'rbc'
            self.size = len(self.txt)


    def remove_digits(self, txt):
        """
        removes digits, quants and dates from txt
        :return: None
        """
        # clear text
        dates_months = re.compile(r'(\d+\s(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря))')
        dates_years = re.compile(r'(\d{4}\sгод.)')
        dates_dots = re.compile(r'( [1-9.]*\d+)')  # all digits with dots inside
        regex_arr = [dates_months, dates_years, dates_dots]
        for regex in regex_arr:
            txt = re.sub(regex, '', txt)
        return txt
    def text_to_vector(self,l_obj=None):
        """
        clears text and fill index dictionary with word-count% format
        :return: None
        """
        self.vector = {}  # index dictionary with word-count% format
        # clearing block
        exp_arr = [r'(&[^;]+;)',r'(<[^>]+>)']
        txt = self.header + self.txt
        for str in exp_arr:
            exp = re.compile(str)
            txt = re.sub(exp,' ',txt)
        txt = txt.replace('  ',' ')
        txt = txt.replace('\n',' ')
        txt = self.remove_digits(txt)
        txt = sf.clear_string(txt,sf.rus_letters+sf.lat_letters+' '+'-'+r'\n')
        txt = txt.lower()

        txt_arr = self._text_to_arr(txt)
        txt_arr = self._remove_prepositions(txt_arr)

        if l_obj:
            stam_arr = []
            for wrd in txt_arr:
                stam_arr.append(l_obj.get_stam(wrd))
        else: stam_arr = txt_arr

        # count words
        for word in txt_arr:
            if self.vector.get(word):
                self.vector[word] += 1
            else:
                self.vector[word] = 1

        # count percent
        # for word in self.vector.keys():
        #    self.vector[word] /= len(txt_arr)

    def get_names(self):
        txt = self.txt.replace('.', ' . ')
        txt_arr = txt.split(' ')
        txt_arr = self._remove_empty_items(txt_arr)
        # !!! define

    def _text_to_arr(self, txt):
        txt_arr = txt.split(' ')
        txt_arr = self._remove_empty_items(txt_arr)
        return txt_arr
    def _remove_empty_items(self, arr):
        new_arr = []
        for item in arr:
            if len(item) != 0: new_arr.append(item)
        return new_arr
    def _remove_prepositions(self, arr):
        """
        removes preposition items from arr
        :param arr: list of words
        :return: cleared arr
        """
        new_arr = []
        for word in arr:
            if not self._is_prep(word):
                new_arr.append(word)
        return new_arr
    def _get_date_time(self):
        """
        gets public_date and public_time from text
        :return:
        """
    def _get_source(self):
        """
        gets agency name from text
        :return:
        """
    def _is_prep(self, word):
        """
        detects if word is a preposition
        :param word: a string
        :return: True/False
        """
        c = self.conn.cursor()
        prep_rows = c.execute("SELECT prep FROM preps WHERE prep='{}'".format(word)).fetchone()
        return (prep_rows != None)

class Distance:
    MIN_MINVECT_SHARE = 0.5
    def count_cosine_1(self, vector1, vector2):
        """
        counts classic cosine distance between texts with common vector space
        :param o_text1, o_text2: Text objects
        :return: cosine distance
        """
        # create common vector space

        mod1 = self._get_vector_module(vector1)
        mod2 = self._get_vector_module(vector2)
        scalar_prod = self._get_scalar_prod(vector1, vector2)
        if mod1 * mod2 > 0:
            return scalar_prod / (mod1 * mod2)
        else:
            return 0

    def count_cosine_2(self, vector1, vector2):
        """
        counts classic cosine distance between texts with  vector space from the shortest text
        :param o_text1, o_text2: Text objects
        :return: cosine distance
        """
        if len(vector1) <= len(vector2):
            min_vect = vector1
            max_vect = vector2
        else:
            min_vect = vector2
            max_vect = vector1
        max_vect = self._minimize_vector(min_vect,max_vect)
        if len(max_vect) / len(min_vect) > self.MIN_MINVECT_SHARE:
            return self.count_cosine_1(max_vect,min_vect)
        else: return 0


    def _get_vector_module(self, v):
        square_sum = 0
        for k in v.keys():
            square_sum += pow(v[k],2)
        return pow(square_sum,0.5)

    def _get_scalar_prod(self, v1, v2):
        # v1, v2 are dictionaries
        prod = 0
        for k in v1.keys():
            if v2.get(k):
                prod += v1[k] * v2[k]
        return prod

    def _minimize_vector(self, min_vect, max_vect):
        # remove key from max_dict if key is absent in min_dict
        new_vect = {}
        for key in max_vect.keys():
            if min_vect.get(key):
                new_vect[key] = max_vect[key]
        return new_vect

class Lemmatizator:
    flexes = []
    def __init__(self,conn_stm):
        c = conn_stm.cursor()
        # get unique flexes
        flexes_rows = c.execute("SELECT DISTINCT flex FROM flexes").fetchall()
        for row in flexes_rows:
            self.flexes.append(row[0])

    def get_stam(self, wrd):
        cnt_flex = len(wrd)
        max_flex = ''
        while cnt_flex > 0:
            cnt_flex -= 1
            cr_flex = wrd[cnt_flex:]
            if cr_flex in self.flexes:
                max_flex = cr_flex
        if max_flex:
            new_stam = wrd[:len(wrd) - len(max_flex)]
        else:
            new_stam = wrd
        return new_stam


class TextRange:
    rbc_texts = []  # of Text objects
    ag_texts = []  # of Text objects

    def move_range(self):
        pass

    def _add_text(self,o_text):

        # add text to an array
        if 'vector' not in dir(o_text):
            print('Not a Text object')
        else:
            if o_text.rbc:
                self.rbc_texts.append(o_text)
            else:
                self.ag_texts.append(o_text)

        # get the closest text from other texts


def get_companies():
    suffixes = ['Inc.', 'Ltd.','AG', 'Holdings', 'International', 'NV']
    p = re.compile(r'([A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*(?=\s+(Inc\.|AG|International|Holdings|NV)))')
    path = 'C:/Kovalenko/news/agences_texts/news1/'
    folders = os.listdir(path)
    total_names = {}
    for folder in folders:
        print(folder)
        files = os.listdir(path + '/' + folder)
        for file in files:
            cur_names = []
            f = open(path + folder + '/' + file, 'r', encoding='utf-8')
            lines = f.readlines()
            if 'loomberg' in lines[0]:
                for line in lines:
                    res = re.findall(p, line)
                    if res:
                        for r in res:
                            name = r[0]
                            if name not in cur_names: cur_names.append(name)
                for name in cur_names:
                    if total_names.get(name):
                        total_names[name]+=1
                    else:
                        total_names[name]=1
                print(len(total_names))
            f.close()

    for name in total_names:
        print(name + ':' + str(total_names[name]))

def get_stamina(words_rows):
    flexes = []
    words = []
    short = words_rows[0][0]
    for w_row in words_rows:
        if len(w_row[0]) < len(short):
            short = w_row[0]
        words.append(w_row[0])
    if len(words) > 1:
        while len(short) > 0:
            flg_cut = False
            for word in words:
                while not short in word:
                    short = short[:-1]
                    flg_cut = True
            if not flg_cut: break
        else:
            pass

        if short:
            for word in words:
                flex = word[len(short):]
                if flex not in flexes:
                    flexes.append(flex)

    return short, flexes

def compare_flexes(short_arr, long_arr):
    for sh_item in short_arr:
        if not sh_item in long_arr:
            return False
    return True

def step1_get_flexes(conn_stm):

    c = conn_stm.cursor()
    new_fam_id = c.execute("SELECT MAX(flexFamID) FROM baseForms").fetchone()[0]

    # load saved flexes
    all_flexes = {} # list of lists
    fam_rows = c.execute("SELECT DISTINCT famID FROM flexes").fetchall()
    for fam_row in fam_rows:
        fam_id = fam_row[0]
        flex_rows = c.execute("SELECT flex FROM flexes WHERE famID={}".format(fam_id)).fetchall()
        flex_fam = []
        for flex_row in flex_rows:
            flex_fam.append(flex_row[0])
        all_flexes[fam_id]= flex_fam


    bf_rows = c.execute('SELECT baseForm, id FROM baseForms WHERE flexFamID=-1').fetchall()
    for row in bf_rows:
        bf = row[0]
        bf_id = row[1]
        if bf:
            words_rows = c.execute("SELECT wrd FROM words WHERE baseForm ='{}'".format(bf)).fetchall()
            stam, flexes = get_stamina(words_rows)
            if flexes:
                # look for similar flexes family
                final_flexFam_id = -1
                for fam_id in all_flexes.keys():
                    if len(flexes) <= len(all_flexes[fam_id]):
                        if compare_flexes(short_arr=flexes, long_arr=all_flexes[fam_id]):
                            # such a flex family exists
                            final_flexFam_id = fam_id
                    else:
                        if compare_flexes(short_arr=all_flexes[fam_id], long_arr=flexes):
                            # old family is a part of a new one
                            c.execute("DELETE FROM flexes WHERE famID={}".format(fam_id))
                            for flex in flexes:
                                c.execute("INSERT INTO flexes (famID,flex) VALUES ({},'{}')".format(fam_id,flex))
                                final_flexFam_id = fam_id

                if final_flexFam_id == -1:
                    new_fam_id +=1
                    final_flexFam_id = new_fam_id
                    for flex in flexes:
                        c.execute("INSERT INTO flexes (famID,flex) VALUES ({},'{}')".format(final_flexFam_id, flex))
                    all_flexes[new_fam_id] = flexes
                c.execute("UPDATE baseForms SET flexFamID={} WHERE id={}".format(final_flexFam_id, bf_id))
                c.execute("UPDATE baseForms SET stam={} WHERE id={}".format(stam, bf_id))
            else:
                c.execute("UPDATE baseForms SET flexFamID=-2 WHERE id={}".format(bf_id))

            conn_stm.commit()
            print(bf)

def step2_precise_effectivness(conn_stm):
    flexes = []
    c = conn_stm.cursor()

    # get unique flexes
    flexes_rows = c.execute("SELECT DISTINCT flex FROM flexes").fetchall()
    for row in flexes_rows:
        flexes.append(row[0])

    cnt_guess = 0
    cnt_try = 0
    wrd_rows = c.execute("SELECT wrd,baseForm FROM words").fetchall()
    for row in wrd_rows:
        cnt_try += 1
        wrd = row[0]
        bf = row[1]
        stam_rows = c.execute("SELECT stam FROM baseForms WHERE baseForm='{}' AND flexFamID > 0".format(bf)).fetchone()
        if stam_rows:
            stam = stam_rows[0]

            # detect maximum flex
            cnt_flex = len(wrd)
            max_flex = ''
            while cnt_flex > 0:
                cnt_flex -= 1
                cr_flex = wrd[cnt_flex:]
                if cr_flex in flexes:
                    max_flex = cr_flex
            if max_flex:
                new_stam = wrd[:len(wrd)-len(max_flex)]
                if new_stam == stam:
                    cnt_guess += 1
                    print(str(cnt_guess/cnt_try*100))

def step3_ag_prepare_texts(file_path,conn):
    c = conn.cursor()
    cat_exp = re.compile(r'^Category: (.+)')
    date_exp = re.compile((r'^Date: (.+)'))
    header_exp = re.compile(r'^Header: (.+)')

    folders = os.listdir(file_path)
    for folder in folders:
        print(folder)
        files = os.listdir(file_path + folder)
        cnt_files = 0
        for file in files:
            cnt_files += 1
            print(file)
            f = open(file_path + folder + '/' + file, 'r', encoding='utf-8')
            lines = f.readlines()
            dt = cat = header = ''
            for line in lines:
                cat_match = re.match(cat_exp, line)
                if cat_match:
                    cat = cat_match.group(1)
                date_match = re.match(date_exp, line)
                if date_match:
                    dt = date_match.group(1)
                header_match = re.match(header_exp, line)
                if header_match:
                    header = header_match.group(1)

            # o_dt = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
            # base_dt = datetime.strptime('2017-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
            # diff_days = o_dt - base_dt
            # diff_seconds = diff_days.days * 24 * 3600 + diff_days.seconds
            # c.execute("INSERT INTO files (name,source,time) VALUES ('{}','{}',{})".format(folder + '/' + file,cat,diff_seconds))
            c.execute("UPDATE files_ag SET header='{}' WHERE name='{}'".format(header, folder + '/' + file))
            conn.commit()
            if cnt_files %100 == 0:
                conn.commit()
        conn.commit()

def step4_prepare_rbc_texts(conn):
    c = conn.cursor()
    dt_changes = {'янв':'01','фев':'02','мар':'03','апр':'04','мая':'05','июн':'06','июл':'07','авг':'08','сен':'09','окт':'10','ноя':'11','дек':'12'}

    dt_rows = c.execute('SELECT id,dt FROM links WHERE time IS NULL').fetchall()
    for row in dt_rows:
        id = row[0]
        dt = row[1]
        if dt:
            for k in dt_changes:
                if k in dt:
                    dt = dt.replace(k + ',', dt_changes[k])
                    break
            if '2017' in dt:
                o_dt = datetime.strptime(dt + ':00', '%d %m %Y %H:%M:%S')
                base_dt = datetime.strptime('2017-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
                diff_days = o_dt - base_dt
                diff_seconds = diff_days.days * 24 * 3600 + diff_days.seconds
                c.execute("UPDATE links SET time={} WHERE id={}".format(diff_seconds,id))
                print(id)
                conn.commit()

def step5_count_distances_test(conn, f_ag_path, f_rbc_path, conn_stm):

    c = conn.cursor()
    rbc_texts = []
    ag_texts = []
    time_ranges = [[13000,14500]]
    d_obj = Distance()
    l_obj = Lemmatizator(conn_stm)
    for tr in time_ranges:
        start_time = tr[0]
        end_time = tr[1]
        # read file paths
        rbc_files_rows = c.execute('SELECT id FROM files_rbc WHERE time >= {} AND time <= {}'.format(start_time,end_time)).fetchall()
        for row in rbc_files_rows:
            path = f_rbc_path+str(row[0])+'.txt'
            t = Text(path,conn,1,int(row[0]))
            t.text_to_vector(l_obj)
            rbc_texts.append(t)

        ag_files_rows = c.execute('SELECT name,id FROM files_ag WHERE time >= {} AND time <= {}'.format(start_time,end_time)).fetchall()
        for row in ag_files_rows:
            path = f_ag_path+row[0]
            t = Text(path,conn,0,int(row[1]))
            t.text_to_vector(l_obj)
            ag_texts.append(t)

        for ag_t in ag_texts:
            # get max similar rbc text
            if ag_t.txt:
                rbc_max_sim_path = ag_max_sim_path = ''
                max_sim = 0
                rbc_max_sim_id = -1
                for rbc_t in rbc_texts:
                    sim = d_obj.count_cosine_1(ag_t,rbc_t)
                    if sim > max_sim:
                        max_sim = sim
                        rbc_max_sim_id = rbc_t.id
                        rbc_max_sim_path = rbc_t.path
                        ag_max_sim_path = ag_t.path
                if max_sim > 0:
                    print('{}-{}:{}'.format(ag_t.path,rbc_max_sim_path,max_sim))
                    c.execute("INSERT INTO similarity (ag_id,rbc_id,sim,ag_path) VALUES ({},{},{},'{}')".format(ag_t.id,rbc_max_sim_id,max_sim,ag_max_sim_path))
                    conn.commit()
            else:
                print('{} is wrong encoding'.format(ag_t.path))

def step6_prepair_similarity(conn):
    c = conn.cursor()
    sim_rows = c.execute('SELECT id,rbc_id,ag_id FROM similarity').fetchall()
    for row in sim_rows:
        sim_id = row[0]
        sim_rbc_id = row[1]
        sim_ag_id = row[2]
        q = 'SELECT rbc_id FROM pairs WHERE ag_id = {} AND rbc_id = {}'.format(sim_ag_id, sim_rbc_id)
        pairs_id = c.execute(q).fetchone()
        if pairs_id:
            c.execute('UPDATE similarity SET is_in_pairs1 = 1 WHERE id = {}'.format(sim_id))
            conn.commit()

def step7_get_f_measure(conn):
    SIM_STEP = 0.1
    BETA = 0.5
    c = conn.cursor()

    def get_count(c, sim, is_in_pairs, sign):
        # sign could be '<' or '>='
        i = 0
        rows = c.execute('SELECT id FROM similarity WHERE sim2 {} {} AND is_in_pairs = {}'.format(sign, sim, is_in_pairs)).fetchall()
        for row in rows: i += 1
        return i

    print('sim;tp;tn;fp;fn;prec;recall;fm')
    for sim in np.arange(0.0, 1.0, SIM_STEP):
        tp = get_count(c,sim,1,'>=')
        tn = get_count(c,sim,0,'<')
        fp = get_count(c,sim,0,'>=')
        fn = get_count(c,sim,1,'<')
        if tp + fp > 0:
            precision = tp / (tp + fp)
        else: precision = 1
        if tp + fn > 0:
            recall = tp / (tp + fn)
        else: recall = 1
        if precision > 0:
            fm = ((1+pow(BETA,2))*precision*recall)/(pow(BETA,2)*precision+recall)
        else: fm = 0
        print(str.replace('{};{};{};{};{};{};{};{}'.format(sim,tp,tn,fp,fn,precision,recall,fm),'.',','))

def step8_count_distances_test_2(conn, f_ag_path, f_rbc_path, conn_stm):

    c = conn.cursor()
    rbc_texts = []
    ag_texts = []
    time_ranges = [[13000,14500]]
    d_obj = Distance()
    l_obj = Lemmatizator(conn_stm)
    for tr in time_ranges:
        start_time = tr[0]
        end_time = tr[1]
        # read file paths
        rbc_files_rows = c.execute('SELECT id FROM files_rbc WHERE time >= {} AND time <= {}'.format(start_time,end_time)).fetchall()
        for row in rbc_files_rows:
            path = f_rbc_path+str(row[0])+'.txt'
            t = Text(path,conn,1,int(row[0]))
            t.text_to_vector(l_obj)
            rbc_texts.append(t)
        print('RBC texts: {}'.format(len(rbc_texts)))
        ag_files_rows = c.execute('SELECT name,id FROM files_ag WHERE time >= {} AND time <= {}'.format(start_time,end_time)).fetchall()
        for row in ag_files_rows:
            path = f_ag_path+row[0]
            t = Text(path,conn,0,int(row[1]))
            t.text_to_vector(l_obj)
            ag_texts.append(t)
        print('AG texts: {}'.format(len(ag_texts)))

        for ag_t in ag_texts:
            # get max similar rbc text
            if ag_t.txt:
                rbc_max_sim_path = ag_max_sim_path = ''
                max_sim = 0
                rbc_max_sim_id = -1
                for rbc_t in rbc_texts:
                    sim = d_obj.count_cosine_2(ag_t.vector,rbc_t.vector)
                    if sim > max_sim:
                        max_sim = sim
                        rbc_max_sim_id = rbc_t.id
                        rbc_max_sim_path = rbc_t.path
                        ag_max_sim_path = ag_t.path
                if max_sim > 0:
                    rows = c.execute('SELECT id FROM similarity WHERE ag_id = {} AND rbc_id = {}'.format(ag_t.id, rbc_max_sim_id)).fetchone()
                    if rows:
                        row_id = rows[0]
                        c.execute('UPDATE similarity SET sim2 = {} WHERE id = {}'.format(max_sim,row_id))
                        print('{}-{}:{} !!{}'.format(ag_t.path, rbc_max_sim_path, max_sim,row_id))
                    else:
                        c.execute("INSERT INTO similarity (ag_id,rbc_id,sim2,ag_path) VALUES ({},{},{},'{}')".format(ag_t.id,rbc_max_sim_id,max_sim,ag_max_sim_path))
                        print('{}-{}:{} !!NEW'.format(ag_t.path, rbc_max_sim_path, max_sim))
                    conn.commit()
            else:
                print('{} is wrong encoding'.format(ag_t.path))

def step10_fill_rbc_headers_sizes(conn):
    c = conn.cursor()

    rows = c.execute('SELECT id FROM files_rbc')
    for row in rows.fetchall():
        id = row[0]
        t = Text(f_rbc_path + str(id) + '.txt', _rbc=True)
        print(t.header, t.size)
        if t.header: c.execute("UPDATE files_rbc SET header = '{}' WHERE id = {}".format(t.header,id))
        if t.size: c.execute(("UPDATE files_rbc SET size = {} WHERE id = {}".format(t.size,id)))
    conn.commit()

def step11_fill_ag_sizes(conn):
    i = 0
    c = conn.cursor()
    ag_files_rows = c.execute('SELECT name,id FROM files_ag WHERE size is null').fetchall()
    for row in ag_files_rows:
        i += 1
        path = f_ag_path + row[0]
        t = Text(path, conn, 0, int(row[1]))
        c.execute('UPDATE files_ag SET size = {} WHERE id = {}'.format(t.size, t.id))
        if i % 1000 == 0:
            print(i)
            conn.commit()

def step12_print_timerange_headers(conn):
    c = conn.cursor()
    time_ranges = [[13000, 14500]]
    for tr in time_ranges:
        start_time = tr[0]
        end_time = tr[1]
        # read file paths
        rbc_files_rows = c.execute('SELECT id, header FROM files_rbc WHERE time >= {} AND time <= {}'.format(start_time, end_time)).fetchall()
        for row in rbc_files_rows:
            print('{};{}'.format(row[0],row[1]))
        print('+++++++++++++++++')
        ag_files_rows = c.execute('SELECT id,header,source FROM files_ag WHERE time >= {} AND time <= {}'.format(start_time, end_time)).fetchall()
        for row in ag_files_rows:
            print('{}|{}|{}'.format(row[0],row[2],row[1]))



dbPath = r'C:\Kovalenko\data_center\dbases\news.db'
dbPath_rbc = r'C:\Kovalenko\data_center\dbases\mediaLinks.db'
dbStaminas = r'C:\Kovalenko\data_center\dbases\staminas.db'
f_ag_path = 'C:/Kovalenko/news/agences_texts/news/'
f_rbc_path = 'C:/Kovalenko/news/rbc_texts/'
test_path1 = 'C:/Kovalenko/news/4832245656598281125.txt'
test_path2 = 'C:/Kovalenko/news/44741.txt'


conn = lite.connect(dbPath)
conn_stm = lite.connect(dbStaminas)
conn_rbc = lite.connect(dbPath_rbc)

# step2_precise_effectivness(conn_stm)
# step3_prepare_texts(file_path, conn)
# step4_prepare_rbc_texts(conn_rbc)
# step5_count_distances_test(conn,f_ag_path,f_rbc_path,conn_stm)
# step6_prepair_similarity(conn)
# step7_get_f_measure(conn)
# step8_count_distances_test_2(conn,f_ag_path,f_rbc_path,conn_stm)
# step10_fill_rbc_headers_sizes(conn)
step11_fill_ag_sizes(conn)
#step12_print_timerange_headers(conn)

# path = 'C:/Kovalenko/news/agences_texts/news/1/6426739333120244601.txt'
# t = Text(path,conn,0,0)
# t.text_to_vector()

# file = open(path,'r')
# lines = file.readlines()
# pass

# t1 = Text(test_path1,_rbc=0,_conn = conn)
# t1.text_to_vector()
# t2 = Text(test_path2, _rbc=1, _conn=conn)
# t2.text_to_vector()
# d = Distance()
# print(d.count_cosine_2(t1.vector,t2.vector))
# t.remove_digits()
# t.text_to_vector()




pass

